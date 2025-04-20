# 🔧 ssm – Simple EC2 SSM CLI
ssm is a lightweight Python CLI tool to interact with AWS EC2 instances over Systems Manager (SSM). It helps you quickly list, connect to, and manage EC2 instances using AWS named profiles, with support for session persistence (remembers your last-used profile and instance).

## 🚀 Features
- 🔍 List EC2 instances with optional filters

- 🔌 Connect to an instance via AWS SSM

- 📦 Send commands to a remote instance

- 🔁 Port forwarding through SSM tunnel

---

## 🛠 Installation
1. Clone the repo:

```bash
git clone https://github.com/your-username/ssm.git
cd ssm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install the CLI globally:
```bash
make install
```

Now you can run ssm from anywhere!

---

## 🧑‍💻 Usage
```bash
ssm [COMMAND] [OPTIONS]
```

## 📄 List EC2 Instances
```bash
ssm list-instances --profile myprofile
```
Optional filters:

- `--tag Name=web` – filter by tag

- `--search "webserver"` – fuzzy search by name or ID

---

## 🔌 Connect to an EC2 Instance via SSM

```bash
ssm connect --instance-id i-0abcd1234efgh5678 --profile myprofile
```

If you omit `--instance-id`, it will use the last connected instance.

## 📦 Send a Command

```bash
ssm send-command --instance-id i-0abcd1234efgh5678 --command "uptime" --profile myprofile
```

## 🔁 Port Forwarding
Forward local port 8080 to remote port 3000:
```bash
ssm port-forward --instance-id i-0abcd1234efgh5678 --local-port 8080 --remote-port 3000 --profile myprofile
```

## 📋 List AWS Named Profiles

```bash
ssm list-profiles
```

---

## 🧠 Session Memory
This tool remembers your last-used:

- AWS named profile

- EC2 instance ID

So you can omit them in future commands for convenience.

---

## 📁 Project Structure

```bash
ssm/
├── cli.py          # Argument parser setup
├── main.py         # CLI entrypoint (contains main logic)
├── utils/
│   └── ec2.py      # EC2 + SSM utility functions
├── config.py       # Stores/retrieves last-used profile & instance
├── Makefile        # Optional CLI installer
├── requirements.txt
└── README.md
```

---

## 🧪 Example Workflow
```bash
ssm list-profiles
ssm list-instances --profile dev
ssm connect --instance-id i-1234567890abcdef
ssm send-command --command "df -h"
ssm port-forward --local-port 8080 --remote-port 8000
```

## 📜 License
MIT licence