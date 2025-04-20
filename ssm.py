from cli import build_parser
import utils.ec2 as ec2
from config import get_last_used, update_last_used

def main():
    parser = build_parser()
    args = parser.parse_args()

    # Load last used profile/instance if not provided
    last_profile, last_instance = get_last_used()
    profile = getattr(args, 'profile', None) or last_profile
    instance_id = getattr(args, 'instance_id', None) or last_instance

    if args.command == 'list-instances':
        ec2.list_instances(
            profile=profile,
            tag_filter=getattr(args, 'tag', None),
            search=getattr(args, 'search', None)
        )
        if profile:
            update_last_used(profile=profile)

    elif args.command == 'connect':
        if not instance_id:
            print("Instance ID not provided and no last-used instance found.")
            return
        ec2.connect_to_instance(instance_id, profile=profile)
        update_last_used(profile=profile, instance_id=instance_id)

    elif args.command == 'send-command':
        if not instance_id:
            print("Instance ID not provided and no last-used instance found.")
            return
        ec2.send_command(instance_id, args.command, profile=profile)
        update_last_used(profile=profile, instance_id=instance_id)

    elif args.command == 'port-forward':
        if not instance_id:
            print("Instance ID not provided and no last-used instance found.")
            return
        ec2.port_forward(instance_id, args.local_port, args.remote_port, profile=profile)
        update_last_used(profile=profile, instance_id=instance_id)

    elif args.command == 'list-profiles':
        ec2.list_profiles()

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
