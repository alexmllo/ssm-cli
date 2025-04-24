# 🔧 ssm – Simple EC2 SSM CLI
ssm is a lightweight Python CLI tool to interact with AWS EC2 instances over Systems Manager (SSM). It helps you quickly list, connect to, and manage EC2 instances using AWS named profiles, with support for session persistence (remembers your last-used profile and instance).

## 🚀 Features
- 🔌 Connect to an instance via AWS SSM

- 📦 Send commands to a remote instance

- 🔁 Port forwarding through SSM tunnel

- 🔁 Port forwarding to remote host through SSM tunnel

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
Available commands:

- `send-command` – Run a shell command on an instance

- `port-forward` – Start local port forwarding

- `port-forward-remote` – Forward a port from the instance to another destination

- (none) – If no command is given, opens an interactive SSM shell

## 📄 List EC2 Instances
```bash
ssm list-instances --profile myprofile
```

## 📦 Send a Command

```bash
ssm send-command --instance i-0abcd1234efgh5678 --command "uptime" --profile myprofile
```

## 🔁 Port Forwarding
Forward local port 8080 to remote port 3000:
```bash
ssm port-forward -i i-0abcd1234efgh5678 --local-port 8080 --remote-port 3000 --profile myprofile
```

## 🔁 Port Forwarding to remote host
Forward local port to remote port and host via an instance:
```bash
ssm port-forward-remote --instance i-0abcd1234efgh5678 --local-port 8080 --remote-port 3000 --host host --profile myprofile
```

---


## 📁 Project Structure

```bash
ssm/
├── cli.py
├── main.py
├── utils/
│   └── ec2.py
├── Makefile
├── requirements.txt
└── README.md
```

---

## 🧪 Example Workflow
```bash
ssm -p prifle-name
ssm connect -i i-1234567890abcdef
ssm send-command -i instance_name --command "df -h"
ssm port-forward -i instance_id --local-port 8080 --remote-port 8000
ssm port-forward-remote -i instance_id --local-port 8080 --remote-port 8000 --host host_name
```

## 📜 License
MIT licence