# 🔧 ssm – Simple EC2 SSM CLI
ssm is a lightweight Python CLI tool to interact with AWS EC2 instances over Systems Manager (SSM). It helps you quickly list, connect to, and manage EC2 instances using AWS named profiles.

## 🚀 Features
- 🔌 Connect to EC2 instances via AWS SSM (interactive shell)
- 📦 Send commands to one or more EC2 instances in parallel
- 📊 Live progress bars and output summaries for batch commands
- 🔁 Port forwarding through SSM tunnel
- 🛰️ Forward to remote hosts via the EC2 tunnel

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
make build
make install
```

Now you can run ssm from anywhere!

---

## 🧑‍💻 Usage
If not globally installed:
```bash
python3 ssm.py [COMMAND] [OPTIONS]
```
If installed globally:
```bash
ssm [COMMAND] [OPTIONS]
```

Available commands:

- `send-command` – Run a shell command on an instance

- `port-forward` – Start local port forwarding

- `port-forward-remote` – Forward a port from the instance to another destination

- (none) – If no command is given, opens an interactive SSM shell

## 📦 Send a Command
Run a shell command on one or more instances:
```bash
ssm send-command -i i-0123 i-0456 -p myprofile -c 'echo "hello world"'
```
You can also pass instance names (resolved by tag Name):
```bash
ssm send-command -i instance-name-1 instance-name-2 -p myprofile -c "uptime"
```

## 🔁 Port Forwarding
Forward a local port to the EC2 instance:
```bash
ssm port-forward -i i-0abcd1234efgh5678 --local-port 8080 --remote-port 3000 --profile myprofile
```

## 🔁 Port Forwarding to remote host
Forward local port to a remote host:port via the EC2 instance:
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


```

## 📜 License
MIT licence