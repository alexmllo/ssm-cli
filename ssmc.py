import argparse
import sys
from utils.ecs import ECSClient
import boto3

def build_parser():
    parser = argparse.ArgumentParser(
        description="🛠️ ssmc: Simplified AWS SSM ECS Container interaction",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  ssmc -p myprofile -c my-cluster -s my-service
  ssmc -p myprofile -c my-cluster
  ssmc port-forward -p myprofile -c my-cluster -s my-service -P 9999:9000
"""
    )

    parser.add_argument(
        "command",
        metavar="COMMAND",
        help="Available commands:\n"
             "  port-forward         Start port forwarding to a container\n"
             "\nIf omitted, opens an interactive shell via SSM.",
        choices=["port-forward"],
        nargs="?",
        default=None
    )

    parser.add_argument(
        "-c", "--cluster",
        help="ECS cluster name",
        required=False
    )

    parser.add_argument(
        "-s", "--service",
        help="ECS service name (optional)",
        required=False
    )

    parser.add_argument(
        "-p", "--profile",
        help="AWS named profile to use (required)",
        required=True
    )

    parser.add_argument(
        "-P", "--port",
        help="Port mapping for forwarding, format: LOCAL:REMOTE (e.g. 9000:9000)",
        required=False
    )

    parser.add_argument(
        "--shell",
        help="Shell to use in the container (default: bash)",
        default="bash",
        required=False
    )

    parser.add_argument(
        "-r", "--region",
        help="AWS region to use (defaults to profile's region)",
        required=False
    )

    return parser

def multichoice(list_of_items: list, item_type: str = "item") -> str:
    """
    Display a list of items and let the user select one.

    :param list_of_items: List of items to choose from
    :param item_type: Type of items being selected (e.g., "cluster", "service", "task")
    :return: The selected item
    """
    if not list_of_items:
        print(f"❌ No {item_type}s found.")
        sys.exit(1)

    if len(list_of_items) == 1:
        if item_type == "task":
            print(f"🔎 Only one {item_type} found: {list_of_items[0]['display']}")
            return list_of_items[0]
        print(f"🔎 Only one {item_type} found: {list_of_items[0]}")
        return list_of_items[0]

    # Sort items alphabetically
    if item_type == "task":
        list_of_items.sort(key=lambda x: x['display'])
    else:
        list_of_items.sort()

    # Display the available items to choose from
    print(f"\nAvailable {item_type}s:")
    for index, item in enumerate(list_of_items, 1):
        if item_type == "task":
            print(f"{index}.\t\t {item['display']}")
        else:
            print(f"{index}.\t\t {item}")

    # Get user input
    while True:
        try:
            choice = input(f"\n➡️ Select a {item_type} by number: ").strip()
            if not choice:
                print("❌ No selection made.")
                continue

            choice_num = int(choice)
            if 1 <= choice_num <= len(list_of_items):
                if item_type == "task":
                    return list_of_items[choice_num - 1]
                return list_of_items[choice_num - 1]
            else:
                print(f"❌ Invalid selection. Please choose a number between 1 and {len(list_of_items)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user...")
            sys.exit(0)

def main():
    parser = build_parser()
    args = parser.parse_args()

    # CHECK PROFILE
    available_profiles = boto3.Session().available_profiles

    if args.profile in available_profiles:
        profile = args.profile
    else:
        print(f"❌ ERROR: Profile '{args.profile}' not found in available AWS profiles.")
        print(f"Available profiles: {', '.join(available_profiles)}")
        parser.print_help()
        sys.exit(1)

    ecs_client = ECSClient(profile=profile, region=args.region)

    #############################
    # 1. Get cluster if necessary
    cluster = args.cluster
    if not cluster:
        clusters = ecs_client.get_clusters()
        cluster = multichoice(clusters, "cluster")

    #############################
    # 2. Get service if necessary
    service = args.service
    if not service:
        services : list[str] = ecs_client.get_services(cluster)
        service = multichoice(services, "service")

    #############################
    # Process flags
    if args.command == "port-forward":
        if not args.port:
            print("❌ Ports are required for port-forward (-p / --port)")
            sys.exit(1)
        
        local_port, remote_port = map(int, args.port.split(':'))
        tasks = ecs_client.get_tasks_by_cluster(cluster, service)
        
        task = multichoice(tasks, "task")
        ecs_client.start_port_forwarding(cluster, task['task_arn'], local_port, remote_port)

    elif args.command == None:
        # Default to interactive shell
        tasks = ecs_client.get_tasks_by_cluster(cluster, service)
        
        task = multichoice(tasks, "task")
        ecs_client.start_session(cluster, task['task_arn'], args.shell)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user...")
        sys.exit(0)
