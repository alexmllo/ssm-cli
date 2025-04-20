import argparse

def build_parser():
    parser = argparse.ArgumentParser(prog="ssm", description="Interact with EC2 via SSM")
    subparsers = parser.add_subparsers(dest="command")

    # List instances command
    list_parser = subparsers.add_parser("list-instances", help="List EC2 instances")
    list_parser.add_argument(
        "--profile",
        help="AWS profile to use",
    )

    # Connect (SSM shell)
    connect_parser = subparsers.add_parser("connect", help="Connect to an EC2 instance via SSM")
    connect_parser.add_argument(
        "--instance_id",
        help="The ID of the EC2 instance to connect to",
        required=True
    )
    connect_parser.add_argument(
        "--profile",
        help="AWS profile to use",
    )

    # Send command
    send_command_parser = subparsers.add_parser("send-command", help="Send a command to an EC2 instance")
    send_command_parser.add_argument(
        "--instance_id",
        help="The ID of the EC2 instance to send the command to",
    )
    send_command_parser.add_argument(
        "--command",
        help="The command to send to the EC2 instance",
        required=True
    )
    send_command_parser.add_argument(
        "--profile",
        help="AWS profile to use",
    )

    # Port forwarding
    port_forward_parser = subparsers.add_parser("port-forward", help="Set up port forwarding to an EC2 instance")
    port_forward_parser.add_argument(
        "--instance_id",
        help="The ID of the EC2 instance to forward ports to",
        required=True
    )
    port_forward_parser.add_argument(
        "--local_port",
        help="The local port to forward to the EC2 instance",
        type=int,
        required=True
    )
    port_forward_parser.add_argument(
        "--remote_port",
        help="The remote port on the EC2 instance to forward to",
        type=int,
        required=True
    )
    port_forward_parser.add_argument(
        "--profile",
        help="AWS profile to use",
    )
    # Update list-instances
    list_parser.add_argument('--tag', help='Filter by tag (e.g., Name=backend)')
    list_parser.add_argument('--search', help='Fuzzy search by name or ID')

    # List profiles
    subparsers.add_parser("list-profiles", help="List AWS profiles")

    return parser