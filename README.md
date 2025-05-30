# SSM and SSMC - AWS Systems Manager CLI Tools

A set of Python CLI tools to interact with AWS EC2 instances and ECS containers over Systems Manager (SSM). These tools help you quickly list, connect to, and manage AWS resources using AWS named profiles.

## Overview

SSM and SSMC are interactive CLI tools that leverage AWS Systems Manager Session Manager to provide secure access to your AWS resources. They allow you to:
- Connect to EC2 instances and ECS containers without opening inbound ports
- Send commands to multiple instances in parallel
- Set up port forwarding through SSM tunnels
- Manage ECS containers with interactive shells
- Transfer files securely using SCP

## Prerequisites

### EC2 Instances
- [Required] AWS SSM agent installed on EC2 instances
- [Required] IAM role with `AmazonSSMManagedInstanceCore` policy attached
- [Required] For SSH/SCP features: SSM agent version 2.3.672.0 or later

### ECS Containers
- [Required] ECS tasks must have the necessary IAM permissions for SSM
- [Required] Container must have a shell available (bash by default)

### User Permissions
Required IAM permissions:
- `ec2:DescribeInstances`
- `ssm:StartSession`
- `ssm:TerminateSession`
- `ssm:DescribeSessions`
- `ssm:DescribeInstanceInformation`
- `ssm:DescribeInstanceProperties`
- `ssm:GetConnectionStatus`
- `ecs:ListClusters`
- `ecs:ListServices`
- `ecs:ListTasks`
- `ecs:DescribeTasks`

Optional permissions:
- `ec2:DescribeRegions` (for cross-region operations)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/ssm-cli.git
cd ssm-cli
```

2. Install the tools:
```bash
# Install both tools
make install

# Or install specific tools
make install-ssm    # Install only SSM
make install-ssmc   # Install only SSMC
```

## Usage

### SSM (EC2 Management)

```bash
ssm [COMMAND] [OPTIONS]
```

Available commands:
- `send-command` – Run a shell command on one or more instances
- `port-forward` – Start local port forwarding
- `port-forward-remote` – Forward a port from the instance to another destination
- `ssh` – Connect to an instance via SSH over SSM
- `scp-to` – Copy files to an instance
- (none) – If no command is given, opens an interactive SSM shell

#### Examples

Send a command to multiple instances:
```bash
ssm send-command -i i-0123 i-0456 -p myprofile -c 'echo "hello world"'
```

Port forwarding:
```bash
ssm port-forward -i i-0abcd1234efgh5678 -p 8080:3000 --profile myprofile
```

SSH connection:
```bash
ssm ssh -i i-0abcd1234efgh5678 -k ~/.ssh/id_rsa --profile myprofile
```

### SSMC (ECS Container Management)

```bash
ssmc [COMMAND] [OPTIONS]
```

Available commands:
- `port-forward` – Start port forwarding to a container
- (none) – If no command is given, opens an interactive shell in the container

#### Examples

Connect to a container:
```bash
ssmc -p myprofile -c my-cluster -s my-service
```

Port forwarding to a container:
```bash
ssmc port-forward -p myprofile -c my-cluster -s my-service -P 9999:9000
```

## Project Structure

```
ssm-cli/
├── cli.py          # Common CLI utilities
├── ssm.py          # EC2 instance management
├── ssmc.py         # ECS container management
├── utils/
│   ├── ec2.py      # EC2 client utilities
│   └── ecs.py      # ECS client utilities
├── Makefile        # Build and installation
├── requirements.txt # Python dependencies
└── README.md       # This file
```

## License

MIT License - See [LICENSE](LICENSE) file for details