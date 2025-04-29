import argparse

def build_parser():
    parser = argparse.ArgumentParser(
        description="🛠️ ssm-cli: Simplified AWS SSM EC2 interaction",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  ssm.py send-command -p myprofile -i i-123456 -c "uptime"
  ssm.py port-forward -p myprofile -i web-server -P 8080:80
  ssm.py port-forward-remote -p myprofile -i db-server -P 3306:3306 -d 127.0.0.1
  ssm.py -p devprofile        # Opens interactive SSM session
"""
    )

    parser.add_argument(
        "command",
        metavar="COMMAND",
        help="Available commands:\n"
             "  send-command         Run a shell command on an instance\n"
             "  port-forward         Start local port forwarding to an instance\n"
             "  port-forward-remote  Forward a port from the instance to another destination\n"
             "\nIf omitted, opens an interactive shell via SSM.",
        choices=["send-command", "port-forward", "port-forward-remote"],
        nargs="?",
        default=None
    )

    parser.add_argument(
        "-i", "--instances",
        help="EC2 instance ID(s) or Name(s) (optional if you want to pick manually)",
        nargs="+",
        default=[],
        required=False
    )

    parser.add_argument(
        "-p", "--profile",
        help="AWS named profile to use (required)",
        required=True
    )

    parser.add_argument(
        "-P", "--port",
        help="Port mapping for forwarding, format: LOCAL:REMOTE (e.g. 8080:80)",
        required=False
    )

    parser.add_argument(
        "-d", "--destination",
        help="Destination IP or hostname for remote port-forwarding (e.g. 127.0.0.1)",
        required=False
    )

    parser.add_argument(
        "-c", "--shell_comand",
        help="Shell command to send to the instance (e.g. 'uptime')",
        required=False
    )

    parser.add_argument(
        "-r", "--region",
        help="AWS region to use (defaults to profile's region)",
        required=False
    )

    return parser
