from concurrent.futures import ThreadPoolExecutor, as_completed
from curses import intrflush
from tqdm import tqdm
import os
import sys
import threading
import boto3
import subprocess
from botocore.configloader import load_config

import botocore
import botocore.exceptions

class EC2Client:
    def __init__(self, profile: str, region: str = ""):
        """
        Initializes an EC2Client instance using a specified AWS CLI profile and region.

        This constructor sets up a Boto3 session using the provided AWS profile. It verifies the credentials
        by attempting to call AWS STS `get_caller_identity`. If the credentials are expired or invalid due to 
        AWS SSO, it attempts to re-authenticate using the `source_profile` defined in the AWS config.

        Region selection follows this priority:
        1. The region passed as a parameter (`region`)
        2. The region configured in the AWS profile
        3. Fallback to 'us-east-1' if none is set

        After initialization, the session will have configured EC2 and SSM clients available as `self.ec2` and `self.ssm`.

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

        print("Using profile:", profile)
        print("Using region:", self.region)
        print("")

        self.ec2 = self.session.client("ec2", region_name=self.region)
        self.ssm = self.session.client("ssm", region_name=self.region)
        

    @staticmethod
    def get_source_profile(profile: str) -> str:
        config_path = os.path.expanduser("~/.aws/config")
        config = load_config(config_path)
        section = f"profile {profile}" if profile != "default" else "default"
        return config.get(section, {}).get("source_profile", profile)

    @staticmethod
    def login_to_source_profile(profile: str) -> None:
        profile_name = EC2Client.get_source_profile(profile)
        try:
            subprocess.run(["aws", "sso", "login", "--profile", profile_name], check=True)
        except subprocess.CalledProcessError:
            print("❌ERROR: Something went wrong in the login process. Aborting.")
            sys.exit(1)

    def get_all_instances(self):
        """
        Retrieve all EC2 instances in a specific AWS profile and region.

        :param profile: The AWS profile to use for credentials.
        :param region: The AWS region to query (default is 'us-east-1').
        :return: A list of EC2 instances (dictionaries) in the region.
        """
        # Create an EC2 client
        ec2_client = self.ec2
        
        # Retrieve all instances (you can add filters if needed)
        response = ec2_client.describe_instances()

        # Extract instances from the response
        instances = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append(instance)

        return instances


    def get_instance_id_by_name(self, name: str) -> str | None:
        """
        Returns the instance ID of the first running EC2 instance matching the given Name tag.
        """
        response = self.ec2.describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": [name]},
                {"Name": "instance-state-name", "Values": ["running"]}
            ]
        )

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                return instance["InstanceId"]

        return None
    
    def get_instance_name_by_id(self, instance_id: str) -> str | None:
        """
        Returns the Name tag of the EC2 instance with the given ID.
        """
        response = self.ec2.describe_instances(
            InstanceIds=[instance_id]
        )

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "Name":
                        return tag["Value"]

        return None

    def connect_to_instance(self, instance_id: str) -> None:
        """
        Connects to an EC2 instance using AWS SSM Session Manager.

        :param instance_id: The ID of the EC2 instance to connect to.
        """
        try:
            print(f"🔗 Connecting to instance {instance_id} via SSM...")
            subprocess.run(
                [
                    "aws", "ssm", "start-session",
                    "--target", instance_id,
                    "--profile", self.session.profile_name,
                    "--document-name", "AWS-StartInteractiveCommand",
                    "--region", self.region,
                    "--parameters", "command=[\"sudo -i\"]"
                ],
                check=True
            )
            print(f"✅ Session ended successfully.")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to start session with instance {instance_id}.")
            sys.exit(1)

    
    def send_command(self, instance_ids: list[str], command: str) -> None:
        try:
            response = self.ssm.send_command(
                InstanceIds=instance_ids,
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [command]},
            )
            command_id = response["Command"]["CommandId"]
            print(f"Running command: {command}")
            print(f"Command ID: {command_id}\n")
            print(f"On instances: {', '.join(instance_ids)}")
            print("")
            procede: str = input("➡️  Do you want to proceed? (y/n): ")
            if procede.lower() != "y":
                print("❌ Command execution aborted.")
                sys.exit(1)
            print("")
            print("🔄 Waiting for command to finish on instances...")

            lock = threading.Lock()
            output_results = []
            progress_bars = {}

            # Create tqdm bars
            for idx, inst_id in enumerate(instance_ids):
                progress_bars[inst_id] = tqdm(
                    total=1, desc=f"⏳ {inst_id}", position=idx, leave=False
                )

            def process_one(instance_id):
                # Wait for command to finish
                self.wait_for_command(command_id, instance_id)

                # Retrieve command output
                try:
                    result = self.ssm.get_command_invocation(
                        CommandId=command_id,
                        InstanceId=instance_id
                    )
                    output = result["StandardOutputContent"].strip()
                except Exception as e:
                    output = f"❌ Error retrieving output: {e}"

                # Complete progress bar
                progress_bars[instance_id].update(1)

                # Save output (thread-safe)
                with lock:
                    output_results.append((instance_id, output))

            # Start thread pool
            with ThreadPoolExecutor(max_workers=min(10, len(instance_ids))) as executor:
                futures = [executor.submit(process_one, inst_id) for inst_id in instance_ids]
                for future in as_completed(futures):
                    future.result()

            # Move cursor below the last progress bar
            print("\n" * len(instance_ids))

            # Print outputs in order
            for instance_id, output in output_results:
                instance_name = self.get_instance_name_by_id(instance_id)
                print(f"📦 Output from {instance_id} | {instance_name}:\n{output}\n")

        except botocore.exceptions.ClientError as e:
            print(f"❌ERROR: Failed to send command: {e}")
            sys.exit(1)

    def wait_for_command(self, command_id: str, instance_id: str):
        """
        Waits for the command to complete on the specified instance.
        """
        waiter = self.ssm.get_waiter("command_executed")
        try:
            waiter.wait(
                CommandId=command_id,
                InstanceId=instance_id,
                WaiterConfig={"Delay": 5, "MaxAttempts": 10}
            )
        except botocore.exceptions.WaiterError:
            raise RuntimeError(f"Command execution timed out on instance {instance_id}")

    def get_command_output(self, command_id: str, instance_id: str) -> tuple[str, str]:
        """
        Retrieves the output and error from the executed command on a given instance.
        """
        try:
            response = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            return response.get('StandardOutputContent', ''), response.get('StandardErrorContent', '')
        except Exception as e:
            raise RuntimeError(f"Failed to get output from {instance_id}: {e}")


    def port_forwarding_to_inst(self, instance_id: str, remotePort: int, LocalPortNumber: intrflush) -> None:
        """
        Sets up port forwarding to the specified EC2 instance.

        :param instance_id: The ID of the EC2 instance.
        :param remotePort: The remote port to forward to.
        :param LocalPortNumber: The local port to forward from.
        """
        try:
            print(f"🔄 Setting up port forwarding to instance {instance_id}...")
            print(f"🔄 Port {remotePort} to local port {LocalPortNumber}")
            subprocess.run(
                [
                    "aws", "ssm", "start-session",
                    "--target", instance_id,
                    "--profile", self.session.profile_name,
                    "--document-name", "AWS-StartPortForwardingSession",
                    "--parameters", f"portNumber={remotePort},localPortNumber=${LocalPortNumber}",
                    "--region", self.region
                ],
                check=True
            )
            print(f"✅ Session ended successfully.")
        except subprocess.CalledProcessError:
            print(f"❌ERROR: Failed to set up port forwarding")
            sys.exit(1)

    def port_forwarding_to_remote_host(self, instance_id: str, host: str, remotePort: str, LocalPortNumber: str) -> None:
        """
        Sets up port forwarding to a remote host via the specified EC2 instance.

        :param instance_id: The ID of the EC2 instance.
        :param host: The remote host to forward to.
        :param remotePort: The remote port to forward to.
        :param LocalPortNumber: The local port to forward from.
        """
        try:
            print(f"🔄 Setting up port forwarding to remote host {host} via instance {instance_id}...")
            print(f"🔄 Port {remotePort} to local port {LocalPortNumber}")
            subprocess.run(
                [
                    "aws", "ssm", "start-session",
                    "--target", instance_id,
                    "--profile", self.session.profile_name,
                    "--document-name", "AWS-StartPortForwardingSession",
                    "--parameters", f"host={host},portNumber={remotePort},localPortNumber={LocalPortNumber}",
                    "--region", self.region
                ],
                check=True
            )
            print(f"✅ Session ended successfully.")
        except subprocess.CalledProcessError:
            print(f"❌ERROR: Failed to set up port forwarding")
            sys.exit(1)