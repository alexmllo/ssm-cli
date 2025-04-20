import os
import json

CONFIG_PATH = os.path.expanduser("~/.ssmcli/config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def update_last_used(profile=None, instance_id=None):
    config = load_config()
    if profile:
        config['last_profile'] = profile
    if instance_id:
        config['last_instance'] = instance_id
    save_config(config)

def get_last_used():
    return load_config().get('last_profile'), load_config().get('last_instance')
