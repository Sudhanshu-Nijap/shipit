## Mini Deployment Platform 🚀

A lightweight Platform-as-a-Service (PaaS) that automatically deploys applications from GitHub repositories using Docker and Kubernetes (K3s).

Users submit a GitHub repository, and the platform automatically:

- Clones the repository

- Builds a Docker image

- Pushes the image to Docker Hub

- Deploys the container to Kubernetes

- Exposes the application publicly


This project demonstrates DevOps, container orchestration, and platform engineering concepts.


## Author

Sudhanshu Nijap

DevOps • Platform Engineering • Full Stack Developer
## Prerequisites

Before setting up the platform, ensure you have:

- AWS account
- Docker Hub account
- A purchased domain
- SSH client
- Git installed

Basic knowledge of:
- Docker
- Kubernetes
- Linux commands

## Architecture

                                    User
                                    │
                                    │ Submit GitHub Repo
                                    ▼
                                    FastAPI Deployment API
                                    │
                                    ▼
                                    GitHub Repository
                                    │
                                    ▼
                                    Docker Build
                                    │
                                    ▼
                                    Docker Hub Registry
                                    │
                                    ▼
                                    Kubernetes (K3s)
                                    │
                                    ▼
                                    Traefik Ingress
                                    │
                                    ▼
                                    Public URL



## Tech Stack

| Component        | Usage                   |
| ---------------- | ----------------------- |
| FastAPI          | Backend deployment API  |
| Docker           | Containerization        |
| Docker Hub       | Image registry          |
| Kubernetes (K3s) | Container orchestration |
| Traefik          | Ingress controller      |
| AWS EC2          | Infrastructure          |
## Step 0

- Before deploying the platform, you must update the configuration variables in the code.

- Open the configuration file (usually in the backend where deployments are handled) and replace the placeholder values:
```bash
DOCKER_USERNAME = "DOCKER_USERNAME" 
DOMAIN = "YOUR_DOMAIN"               
DOCKER_REPO = "YOUR_DOCKER_HUB_REPO" 
```

Example:
```bash
DOCKER_USERNAME = "sudhanshunijap"
DOMAIN = "sudhanshunijap.me"
DOCKER_REPO = "shipit"
```

These values are required for the platform to correctly build, push, and expose deployed applications.

1️⃣ Create a Docker Hub Repository

Go to:
```bash
https://hub.docker.com
```
Create a new repository.

Example:
```bash
Repository Name: mini-platform-images
```
Why this is required:

   - Kubernetes does not build images.
   - It pulls images from a container registry.


Without a Docker repository, Kubernetes cannot deploy the application containers.

2️⃣ Buy a Domain

You must purchase a domain for exposing deployed applications.

Recommended providers:

    Namecheap
    Cloudflare
    Google Domains

Example domain:

```bash
sudhanshunijap.me
```

This domain will be used to route traffic to applications deployed in Kubernetes.

3️⃣ Configure DNS

Add an A record pointing to your Elastic IP.

Example:

| Type | Name | Value          |
| ---- | ---- | -------------- |
| A    | @    | EC2 Elastic IP |

Example result:
```bash
sudhanshunijap.me → 43.205.145.248
```
## Step 1 — Create an AWS EC2 Instance


Go to AWS Console → EC2 → Launch Instance

Configuration:

| Setting       | Value               |
| ------------- | ------------------- |
| OS            | Ubuntu 22.04        |
| Instance Type | t2.micro / t3.micro |
| Storage       | 20GB                |
| Key Pair      | Create `.pem` key   |


Download the key file.

Example:
```bash
Demo_Docker.pem
```

## Step 2 — Configure Security Group

Add the following inbound rules.

| Type       | Port |
| ---------- | ---- |
| SSH        | 22   |
| HTTP       | 80   |
| HTTPS      | 443  |
| Custom TCP | 8000 |


Why these ports?

| Port | Purpose        |
| ---- | -------------- |
| 22   | SSH access     |
| 80   | HTTP traffic   |
| 443  | HTTPS          |
| 8000 | FastAPI server |



## Step 3 — Allocate Elastic IP

AWS public IPs change when the instance restarts.

- Elastic IP ensures:

- Stable domain mapping

- Stable HTTPS certificates

- Permanent public endpoint

Go to:

```bash
EC2 → Elastic IPs → Allocate
````

Then associate it with your instance.


## Step 4 — Connect to EC2

```bash
ssh -i "<your_pem_file.pem>" ubuntu@<elastic-ip>
````

Example:

```bash
ssh -i "<your_pem_file.pem>" ubuntu@54.210.xx.xx
````

## Step 5 — Install Docker

```bash
sudo apt update
sudo apt install docker.io -y

sudo systemctl enable docker
sudo systemctl start docker

sudo usermod -aG docker ubuntu

logout
````

```bash
docker ps
````

## Step 6 — Install Kubernetes (K3s)

K3s is a lightweight Kubernetes distribution.

Install it:
```bash
curl -sfL https://get.k3s.io | sh -
```
Check installation:
```bash
sudo kubectl get nodes
```
Expected output:
```bash
Ready control-plane
```
## Step 7 — Configure kubectl

Copy kubeconfig to your user.
```bash
sudo mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown ubuntu:ubuntu ~/.kube/config
````

Set environment variable:
```bash
export KUBECONFIG=/home/ubuntu/.kube/config
```

Verify:
```bash
kubectl get nodes
```

## Step 8 — Install Python Environment

```bash
sudo apt install python3 python3-pip python3-venv -y
```

Clone the project.
```bash
git clone https://github.com/Sudhanshu-Nijap/shipit.git
cd mini_deployment_platform
```

Create virtual environment.
```bash
python3 -m venv env
source env/bin/activate
```

Install dependencies.
```bash
pip install -r requirements.
```
## Step 9 — Docker Hub Login

Login to Docker Hub.

```bash
docker login
```

Why is a Docker registry needed?

    - Kubernetes does not build images.

    - It only pulls images from registries.

Deployment flow:
```bash
Code → Docker Build → Docker Hub → Kubernetes pulls image
```
Without a registry Kubernetes cannot deploy containers.
## Step 10 — Run the Deployment API
Start the backend.
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Access the API documentation.
```bash
http://<elastic-ip>:8000/

```

## Step 13 — HTTPS Setup

If Kubernetes commands fail because of config issues:
```bash
export KUBECONFIG=/home/ubuntu/.kube/config
```
Traefik can automatically generate HTTPS certificates using Let's Encrypt.


## Repository Structure Required for Deployment

Applications must contain a Dockerfile.

Example structure:

    my-app
    │
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py
    │
    ├── app
    │   └── main.py
    │
    └── README.md

    
## Example Dockerfile

    FROM python:3.10-slim

    WORKDIR /app

    COPY requirements.txt .

    RUN pip install -r requirements.txt

    COPY . .

    CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
## Important Deployment Rules

Applications must:

- Include a Dockerfile

- Expose port 8000

- Bind to 0.0.0.0

Example:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```



## Deployment Flow  


When a user submits a repository:
```bash
POST /deploy
```
Example request:
```bash
{
 "github_url": "https://github.com/user/app"
}
```

Internal process:

    1. Clone repository
    2. Build Docker image
    3. Push image to Docker Hub
    4. Generate Kubernetes YAML
    5. Deploy container
    6. Create service
    7. Expose application


## Debugging Errors

No Server Available Error

Sometimes old deployments consume resources.

Delete previous deployments.
```bash
kubectl get deployments
```

Then remove unused apps.
```bash
kubectl delete deployment <deployment-name>
```
Example:
```bash
kubectl delete deployment testapp
```

## Kubernetes Commands Not Working

Run:
```bash
export KUBECONFIG=/home/ubuntu/.kube/config
```


## Docker Permission Error

Fix permissions.
```bash
sudo usermod -aG docker ubuntu
```
Then reconnect to the server.
## SSH Host Key Changed

Run:
```bash
ssh-keygen -R <ec2-host>
```
## Future Improvements


- Dynamic subdomains for deployed apps

- GitHub webhook auto-deploy

- Horizontal Pod Autoscaling

- Multi-node Kubernetes cluster

- Deployment Dashboard

- Auto-detect project type

