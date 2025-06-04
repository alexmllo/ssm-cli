import argparse
import sys
from utils.ecs.ecs import ECSClient
import boto3
from cli import build_ssmc_parser

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
            print(f"🔎 Only one {item_type} found: {list_of_items[0]['Name']} ({list_of_items[0]['Id']})")
            decision = input("Do you want to select this task? (y/n): ").strip()
            if decision == "yes" or decision == "y":
                return list_of_items[0]
            else:
                print("❌ Task selection cancelled.")
                sys.exit(1)
        print(f"🔎 Only one {item_type} found: {list_of_items[0]}")
        return list_of_items[0]

    # Sort items alphabetically
    if item_type == "task":
        list_of_items.sort(key=lambda x: x['Name'])
    else:
        list_of_items.sort()

    # Display the available items to choose from
    print(f"\nAvailable {item_type}s:")
    for index, item in enumerate(list_of_items, 1):
        if item_type == "task":
            print(f"{index}.\t\t {item['Name']} ({item['Id']}) - Created: {item['Time']}")
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
                return list_of_items[choice_num - 1]
            else:
                print(f"❌ Invalid selection. Please choose a number between 1 and {len(list_of_items)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user...")
            sys.exit(0)

def main():
    parser = build_ssmc_parser()
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
        ecs_client.start_port_forwarding(cluster=cluster, task_id=task['Id'], container_id=task['ContainerId'], local_port=local_port, remote_port=remote_port)

    elif args.command == None:
        # Default to interactive shell
        tasks = ecs_client.get_tasks_by_cluster(cluster, service)
        
        task = multichoice(tasks, "task")
        ecs_client.start_session(cluster=cluster, container_name=task['Name'], task_id=task['Id'], shell=args.shell)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user...")
        sys.exit(0)
