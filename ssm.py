import sys

import boto3
from cli import build_ssm_parser
import utils.ec2.ec2 as ec2
import readline

def select_instance(client: ec2.EC2Client, instance_name: str = None) -> str:
    """
    List EC2 instances for the current profile and let the user select one.

    :param client: The EC2Client instance to interact with AWS.
    :param instance_name: Optionally, filter instances by name (if provided).
    :return: The selected instance ID.
    """
    # Get all instances
    instances = client.get_all_instances()
    
    if instance_name:
        # If instance name is provided, filter instances by name
        instances = [inst for inst in instances if instance_name.lower() in inst['Name'].lower()]
    
    # If no instances found
    if not instances:
        print("❌ No instances found.")
        sys.exit(1)

    if len(instances) == 1:
        print(f"🔎 Only one instance found: {instances[0]['Id']} - {instances[0]['Name']}")
        return instances[0]['InstanceId']
    
    # Sort them by their name
    instances.sort(key=lambda x: next((tag['Value'] for tag in x['Tags'] if tag['Key'] == 'Name'), ''))

    # Display the available instances to choose from
    for index, inst in enumerate(instances):
        tags = { x['Key']: x['Value'] for x in inst['Tags'] }
        print(f"{index + 1}.\t\t {inst['InstanceId']}\t\t {tags.get('Name', 'N/A')}")

    # Get user input
    try:
        choice = int(input("\n➡️ Select an instance by number: ").strip()) - 1
        if 0 <= choice < len(instances):
            return instances[choice]['InstanceId']
        else:
            print("❌ Invalid selection.")
            sys.exit(1)
    except (ValueError, IndexError):
        print("❌ Invalid input.")
        sys.exit(1)

def main():
    parser = build_ssm_parser()
    args = parser.parse_args()

    # CHECK PROFILE
    available_profiles = boto3.Session().available_profiles

    if args.profile in available_profiles:
        profile = args.profile
    else:
        print(f"❌ ERROR: Profile '{args.profile}' not found in available AWS profiles.")
        print(f"Available profiles: {', '.join(available_profiles)}")
        print("")
        parser.print_help()
        sys.exit(1)

    client : ec2.EC2Client = ec2.EC2Client(profile=profile, region=args.region)

    # SEND COMMAND
    instances_ids = []
    if args.command == "send-command":
        if not args.shell_comand:
            parser.error("❌ERROR: Shell command is required for send-command.")
        if not args.instances:
            parser.error("❌ERROR: At least one instance is required for send-command.")

        # Resolve instance
        for instance in args.instances:
            if instance.startswith("i-"):
                instances_ids.append(instance)
            else:
                instance_id = client.get_instance_id_by_name(instance)
                if instance_id:
                    instances_ids.append(instance_id)
                else:
                    print(f"❌ERROR: No instance found with name '{instance}'.")
                    sys.exit(1)

        client.send_command(instances_ids, args.shell_comand)

    # SSH
    elif args.command == "ssh":
        if not args.key:
            parser.error("❌ERROR: SSH key is required for SSH.")
        if args.instances > 1:
            parser.error("❌ERROR: Only one instance is allowed for SSH.")
        
        if args.instances:
            instance_id = args.instances[0]
            if instance_id.startswith("i-"):
                instance_id = args.instances[0]
            else:
                instance_id = client.get_instance_id_by_name(instance_id)
        else:
            instance_id = select_instance(client)
        
        client.ssh_to_instance(
            instance_id=instance_id,
            key_path=args.key,
            user=args.user or "ubuntu"
        )

    # PORT FORWARD
    elif args.command == "port-forward":
        if not args.port:
            print("❌ERROR: Ports are required for port-forward.")
            sys.exit(1)
        
        if args.instances > 1:
            parser.error("❌ERROR: Only one instance is allowed for port-forward.")

        # Vlidate port format
        if ":" not in args.port:
            print("❌ERROR: Port format should be 'LOCALPORT:REMOTEPORT'.")
            sys.exit(1)
        
        try:
            local_port, remote_port = map(int, args.port.split(":"))
        except ValueError:
            print("❌ERROR: Invalid port format. Use 'LOCALPORT:REMOTEPORT'.")
            sys.exit(1)

        # Resolve instance
        if args.instances:
            instance = args.instances[0]
            if instance.startswith("i-"):
                instance_id = args.instances
            else:
                instance_id = client.get_instance_id_by_name(instance)
                if not instance_id:
                    print(f"❌ERROR: No instance found with name '{instance}'.")
                    sys.exit(1)
        else:
            instance_id = select_instance(client)

        client.port_forwarding_to_inst(instance_id, remote_port, local_port)

    # PORT FORWARD REMOTE
    elif args.command == "port-forward-remote":
        if not args.port or not args.destination:
            print("❌ERROR: Ports and destination are required for port-forward-remote.")
            sys.exit(1)

        if args.instances > 1:
            parser.error("❌ERROR: Only one instance is allowed for port-forward-remote.")
        
        # Validate port format
        if ":" not in args.port:
            print("❌ERROR: Port format should be 'LOCALPORT:REMOTEPORT'.")
            sys.exit(1)
        
        try:
            local_port, remote_port = map(int, args.port.split(":"))
        except ValueError:
            print("❌ERROR: Invalid port format. Use 'LOCALPORT:REMOTEPORT'.")
            sys.exit(1)
        
        # Resolve instance
        if args.instances:
            instance = args.instances[0]
            if instance.startswith("i-"):
                instance_id = instance
            else:
                instance_id = client.get_instance_id_by_name(instance)
                if not instance_id:
                    print(f"❌ERROR: No instance found with name '{instance}'.")
                    sys.exit(1)
        else:
            instance_id = select_instance(client)
        
        client.port_forwarding_to_remote_host(instance_id, args.destination, remote_port, local_port)

    # SCP TO INSTANCE
    elif args.command == "scp-to":
        if not args.local_path or not args.remote_path:
            parser.error("❌ERROR: Both local and remote paths are required for scp-to.")
        if len(args.instances) > 1:
            parser.error("❌ERROR: Only one instance is allowed for for scp-to.")

        if args.instances:
            instance_id = args.instances[0]
            if not instance_id.startswith("i-"):
                instance_id = client.get_instance_id_by_name(instance_id)
                if not instance_id:
                    print(f"❌ERROR: No instance found with name '{args.instances[0]}'.")
                    sys.exit(1)
        else:
            instance_id = select_instance(client)

        client.scp_to_instance(
            instance_id=instance_id,
            local_path=args.local_path,
            remote_path=args.remote_path,
            key_path=args.key,
            user=args.user
        )

    # SCP FROM INSTANCE
    elif args.command == "scp-from":
        if not args.local_path or not args.remote_path:
            parser.error("❌ERROR: Both local and remote paths are required for scp-from.")
        if len(args.instances) > 1:
            parser.error("❌ERROR: Only one instance is allowed for for scp-from.")

        if args.instances:
            instance_id = args.instances[0]
            if not instance_id.startswith("i-"):
                instance_id = client.get_instance_id_by_name(instance_id)
                if not instance_id:
                        print(f"❌ERROR: No instance found with name '{args.instances[0]}'.")
                        sys.exit(1)
        else:
            instance_id = select_instance(client)

        client.scp_from_instance(
            instance_id=instance_id,
            remote_path=args.remote_path,
            local_path=args.local_path,
            key_path=args.key,
            user=args.user
        )

    # LIST INSTANCES OF A PROFILE
    elif args.command == None:
        # If no command is specified, select an instance and open a shell on it
        if not args.instances:
            instance_id = select_instance(client)

        if len(args.instances) > 1:
            parser.error("❌ERROR: Either one or none instance is allowed for interactive shell.")

        if len(args.instances) == 1:
            if args.instances[0].startswith("i-"):
                instance_id = args.instances[0]
            else:
                instance_id = client.get_instance_id_by_name(instance_id)
                if not instance_id:
                    print(f"❌ERROR: No instance found with name '{instance_id}'.")
                    sys.exit(1)

        # Open a shell on the selected instance (you can implement this if needed)
        print(f"Opening shell on instance {instance_id}...")
        client.connect_to_instance(instance_id)



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user...")
        sys.exit(0)
