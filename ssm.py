import sys
from threading import local
from cli import build_parser
import utils.ec2 as ec2
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
    parser = build_parser()
    args = parser.parse_args()

    profile = args.profile
    client : ec2.EC2Client = ec2.EC2Client(profile=profile, region=args.region)

    if args.command == "send-command":
        if not args.shell_comand:
            print("❌ERROR: Shell command is required for send-command.")
            sys.exit(1)

        # Resolve instance
        if args.instance:
            if args.instance.startswith("i-"):
                instance_id = args.instance  # looks like an EC2 instance ID
            else:
                instance_id = client.get_instance_id_by_name(args.instance)
                if not instance_id:
                    print(f"❌ERROR: No instance found with name '{args.instance}'.")
                    sys.exit(1)
        else:
            instance_id = select_instance(client)

        client.send_command(instance_id, args.shell_comand)

    elif args.command == "port-forward":
        if not args.port:
            print("❌ERROR: Ports are required for port-forward.")
            sys.exit(1)

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
        if args.instance:
            if args.instance.startswith("i-"):
                instance_id = args.instance
            else:
                instance_id = client.get_instance_id_by_name(args.instance)
                if not instance_id:
                    print(f"❌ERROR: No instance found with name '{args.instance}'.")
                    sys.exit(1)
        else:
            instance_id = select_instance(client)

        client.port_forwarding_to_inst(instance_id, remote_port, local_port)

    elif args.command == "port-forward-remote":
        if not args.port or not args.destination:
            print("❌ERROR: Ports and destination are required for port-forward-remote.")
            sys.exit(1)
        
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
        if args.instance:
            if args.instance.startswith("i-"):
                instance_id = args.instance
            else:
                instance_id = client.get_instance_id_by_name(args.instance)
                if not instance_id:
                    print(f"❌ERROR: No instance found with name '{args.instance}'.")
                    sys.exit(1)
        else:
            instance_id = select_instance(client)
        
        client.port_forwarding_to_remote_host(instance_id, args.destination, remote_port, local_port)

    elif args.command == None:

        # If no command is specified, select an instance and open a shell on it
        instance_id = select_instance(client)

        # Open a shell on the selected instance (you can implement this if needed)
        print(f"Opening shell on instance {instance_id}...")
        client.connect_to_instance(instance_id)



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user...")
        sys.exit(0)
