import boto3
from typing import List, Optional, Tuple
import sys
from botocore.configloader import load_config
import os
import subprocess

import botocore
import botocore.exceptions

class ECSClient:
    def __init__(self, profile: str, region: Optional[str] = None):
        """
        Initializes an ECSClient instance using a specified AWS CLI profile and region.

        This constructor sets up a Boto3 session using the provided AWS profile. It verifies the credentials
        by attempting to call AWS STS `get_caller_identity`. If the credentials are expired or invalid due to 
        AWS SSO, it attempts to re-authenticate using the `source_profile` defined in the AWS config.

        Region selection follows this priority:
        1. The region passed as a parameter (`region`)
        2. The region configured in the AWS profile
        3. Fallback to 'us-east-1' if none is set

        After initialization, the session will have configured EC2 and SSM clients available as `self.ecs` and `self.ssm`.

        Parameters:
        ----------
        profile : str
            The AWS CLI profile name to use for authentication and session creation.

        region : str, optional
            The AWS region to operate in. If not provided, the region from the profile configuration is used.
            Defaults to 'us-east-1' if neither is available.

        Raises:
        ------
        SystemExit:
            If the profile is not found or SSO login fails after retrying, the program exits with an error message.
        """
        try:
            self.session = boto3.session.Session(profile_name=profile)
        except botocore.exceptions.ProfileNotFound:
            print(f"Profile {profile} not found. Please check your AWS configuration.")
            sys.exit(1)

        # Verify AWS credentials
        try:
            sts = self.session.client("sts")
            sts.get_caller_identity()
            print("AWS credentials are valid.")
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.UnauthorizedSSOTokenError,
            botocore.exceptions.CredentialRetrievalError
        ):
            print("AWS SSO credentials are expired. Logging in again...")
            self.login_to_source_profile(profile)
        
        self.region = region or self.session.region_name or "eu-west-1"
        self.profile = profile

        print(f"Using profile: {profile}")
        print(f"Using region: {self.region}")
        print("")

        self.ecs = self.session.client("ecs", region_name=self.region)
        self.ssm = self.session.client("ssm", region_name=self.region) 

    @staticmethod
    def get_source_profile(profile: str) -> str:
        """
        Retrieves the source profile from the AWS credentials file.

        :param profile: The profile name to check for source profile.
        :return: The source profile name.
        """
        config_path = os.path.expanduser("~/.aws/credentials")
        credentials = load_config(config_path)
        section = profile if profile != "default" else "default"
        return credentials.get(section, {}).get("source_profile", profile)

    @staticmethod
    def login_to_source_profile(profile: str) -> None:
        """
        Logs in to the source profile using AWS SSO.

        :param profile: The profile name to use for login.
        """
        profile_name = ECSClient.get_source_profile(profile)
        try:
            subprocess.run(["aws", "sso", "login", "--profile", profile_name], check=True)
        except subprocess.CalledProcessError:
            print("❌ERROR: Something went wrong in the login process. Aborting.")
            sys.exit(1)

    def get_clusters(self) -> List[str]:
        """
        List all ECS clusters in the account.
        
        :return: List of cluster ARNs
        """
        try:
            response = self.ecs.list_clusters()
            return [arn.split('/')[-1] for arn in response['clusterArns']]
        except Exception as e:
            print(f"❌ Error listing clusters: {str(e)}")
            sys.exit(1)

    def get_services(self, cluster: str) -> List[str]:
        """
        List all services in a cluster.
        
        :param cluster: The cluster name or ARN
        :return: List of service names
        """
        try:
            response = self.ecs.list_services(cluster=cluster)
            return [arn.split('/')[-1] for arn in response['serviceArns']]
        except Exception as e:
            print(f"❌ Error listing services: {str(e)}")
            sys.exit(1)

    def get_tasks_by_cluster(self, cluster: str, service: Optional[str] = None) -> List[str]:
        """
        Get tasks in a cluster, optionally filtered by service.
        
        :param cluster: The cluster name or ARN
        :param service: Optional service name to filter tasks
        :return: List of task information including task ARN, container name, and status
        """
        try:
            # Ensure cluster is not None
            if not cluster:
                print("❌ Cluster name is required.")
                sys.exit(1)

            # List tasks
            if service:
                tasks = self.ecs.list_tasks(cluster=cluster, serviceName=service)
            else:
                tasks = self.ecs.list_tasks(cluster=cluster)

            if not tasks['taskArns']:
                print(f"❌ No tasks found in cluster {cluster}.")
                sys.exit(1)

            # Get task details to include container information
            task_details = self.ecs.describe_tasks(cluster=cluster, tasks=tasks['taskArns'])
            # Format task information for display
            formatted_tasks: list[dict[str, str]] = []
            for task in task_details['tasks']:
                task_arn = task['taskArn']
                time = task['createdAt']
                task_id = task_arn.split('/')[-1]
                for container in task['containers']:
                    if 'runtimeId' in container:
                        formatted_tasks.append({
                            "Name": container['name'],
                            "Id": task_id,
                            "Time": time,
                            "ContainerId": container['runtimeId'],
                        })
            return formatted_tasks
        except Exception as e:
            print(f"❌ Error getting tasks: {str(e)}")
            sys.exit(1)

    def start_port_forwarding(self, cluster: str, task_id: str, container_id: str, local_port: int, remote_port: int) -> None:
        """
        Start port forwarding to a container.
        
        :param cluster: The cluster name or ARN
        :param task_id: The task ID
        :param container_id: The container ID
        :param local_port: Local port number
        :param remote_port: Remote port number
        """
        try:
            print(f"🔗 Setting up port forwarding {local_port}:{remote_port} to container in task {task_id} ({container_id})...")
            subprocess.run(
                [
                    "aws", "ssm", "start-session",
                    "--target", f"ecs:{cluster}_{task_id}_{container_id}",
                    "--profile", self.profile_name,
                    "--document-name", "AWS-StartPortForwardingSession",
                    "--region", self.region,
                    "--parameters", f"portNumber=[\"{remote_port}\"],localPortNumber=[\"{local_port}\"]"
                ],
                check=True
            )
            print(f"✅ Port forwarding ended successfully.")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to start port forwarding with container in task {task_id} ({container_id}).")
            sys.exit(1)

    def start_session(self, cluster: str, container_name: str, task_id: str, shell: str = "bash") -> None:
        """
        Start an SSM session to a container.
        
        :param cluster: The cluster name or ARN
        :param container_name: The container name
        :param task_id: The task ID
        :param shell: The shell to use (default: bash)
        """
        try:
            print(f"🔗 Connecting to container {task_id} ({container_name}) via SSM...")
            subprocess.run(
                [
                    "aws", "ecs", "execute-command",
                    "--cluster", cluster,
                    "--profile", self.profile,
                    "--container", container_name,
                    "--task", task_id,
                    "--command", shell,
                    "--region", self.region,
                    "--interactive"
                ],
                check=True
            )
            print(f"✅ Session ended successfully.")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to start session with container in task {task_id} ({container_name}).")
            sys.exit(1)