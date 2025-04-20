import boto3
import subprocess

from config import update_last_used

def get_boto_session(profile):
    return boto3.Session(profile_name=profile) if profile else boto3.Session()

def list_profiles():
    import os
    import configparser
    profiles = configparser.ConfigParser()
    profiles.read(os.path.expanduser('~/.aws/config'))
    print("Available AWS profiles:")
    for section in profiles.sections():
        print("-", section.replace("profile ", ""))

def list_instances(profile=None):
    session = get_boto_session(profile)
    ec2 = session.client('ec2')

    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    print("Running instances:")
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            print(f"{instance['InstanceId']} | {instance.get('Tags', [])} | {instance['PrivateIpAddress']}")

def connect_to_instance(instance_id, profile=None):
    cmd = ['aws', 'ssm', 'start-session', '--target', instance_id]
    if profile:
        cmd += ['--profile', profile]
    subprocess.run(cmd)

def send_command(instance_id, command, profile=None):
    session = get_boto_session(profile)
    ssm = session.client('ssm')
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': [command]}
    )
    command_id = response['Command']['CommandId']
    print(f"Sent command. Command ID: {command_id}")

def port_forward(instance_id, local_port, remote_port, profile=None):
    cmd = [
        'aws', 'ssm', 'start-session',
        '--target', instance_id,
        '--document-name', 'AWS-StartPortForwardingSession',
        '--parameters', f'localPort={local_port},remotePort={remote_port}'
    ]
    if profile:
        cmd += ['--profile', profile]
    subprocess.run(cmd)

def fuzzy_match(instance, keyword):
    keyword = keyword.lower()
    tags = instance.get('Tags', [])
    for tag in tags:
        if keyword in tag['Value'].lower():
            return True
    return keyword in instance['InstanceId'].lower()

def list_instances(profile=None, tag_filter=None, search=None):
    session = get_boto_session(profile)
    ec2 = session.client('ec2')

    filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
    if tag_filter:
        k, v = tag_filter.split('=', 1)
        filters.append({'Name': f'tag:{k}', 'Values': [v]})

    response = ec2.describe_instances(Filters=filters)
    results = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if search and not fuzzy_match(instance, search):
                continue
            results.append(instance)

    if not results:
        print("No matching instances found.")
        return

    for i, instance in enumerate(results, 1):
        name = next((t['Value'] for t in instance.get('Tags', []) if t['Key'] == 'Name'), 'N/A')
        print(f"[{i}] {instance['InstanceId']} | {name} | {instance['PrivateIpAddress']}")

    if len(results) == 1:
        update_last_used(profile, results[0]['InstanceId'])