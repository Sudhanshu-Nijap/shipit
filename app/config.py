import os

# Configuration Settings
DOCKER_USERNAME = "sudhanshunijap" # replace with your docker hub username
DOCKER_REPO = "shipit"             # replace with your docker hub repo name
DOMAIN = "sudhanshunijap.me"       # replace with your domain

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOYMENTS_FILE = os.path.join(BASE_DIR, "deployments.json")
