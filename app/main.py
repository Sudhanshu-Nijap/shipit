import os, uuid
import shutil
import zipfile
import json
from datetime import datetime
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.deployer import deploy_project  
from fastapi.responses import StreamingResponse
from app.deployer import generate_k8_yaml
from app.deployer import stream_cmd

from app.config import DOCKER_USERNAME, DOCKER_REPO, DOMAIN, BASE_DIR, DEPLOYMENTS_FILE

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def save_deployment(name, url, deployment_type):
    deployments = []
    if os.path.exists(DEPLOYMENTS_FILE):
        with open(DEPLOYMENTS_FILE, "r") as f:
            try:
                deployments = json.load(f)
            except:
                pass
            
    # Check if exists
    for dep in deployments:
        if dep["id"] == name:
            dep["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(DEPLOYMENTS_FILE, "w") as f:
                json.dump(deployments, f, indent=4)
            return

    deployments.insert(0, {
        "id": name,
        "name": name.rsplit("-", 1)[0],
        "url": url,
        "type": deployment_type,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(DEPLOYMENTS_FILE, "w") as f:
        json.dump(deployments, f, indent=4)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    return templates.TemplateResponse(request=request, name="projects.html")

class DeployRequest(BaseModel):
    github_url: str
    project_name: str

@app.post("/deploy")
def deploy(request: DeployRequest):

    def generator():
        unique_id = str(uuid.uuid4())[:6]
        deployment_name = f"{request.project_name}-{unique_id}"
        project_path = os.path.join(BASE_DIR, deployment_name)
        image_name = f"docker.io/{DOCKER_USERNAME}/{DOCKER_REPO}:{deployment_name}"

        yield "Cloning repository...\n"
        yield from stream_cmd(f"git clone {request.github_url} {project_path}")

        yield "\nBuilding Docker image...\n"
        yield from stream_cmd(f"docker build -t {image_name} {project_path}")

        yield "\nPushing Docker image...\n"
        yield from stream_cmd(f"docker push {image_name}")

        yield "\nGenerating Kubernetes YAML...\n"

        yaml_content = generate_k8_yaml(deployment_name, image_name, DOMAIN)
        yaml_file = os.path.join(BASE_DIR, f"{deployment_name}.yaml")

        with open(yaml_file, "w") as f:
            f.write(yaml_content)

        yield "\nDeploying to Kubernetes...\n"
        yield from stream_cmd(f"kubectl apply -f {yaml_file}")

        yield "\n[SUCCESS] Deployment complete!\n"
        url = f"https://{deployment_name}.{DOMAIN}"
        save_deployment(deployment_name, url, "GitHub")
        yield f"[URL] {url}\n"
        yield f"[ID] {deployment_name}\n"

    return StreamingResponse(generator(), media_type="text/plain")

@app.post("/deploy-zip")
def deploy_zip(project_name: str = Form(...), file: UploadFile = File(...)):

    def generator():
        unique_id = str(uuid.uuid4())[:6]
        deployment_name = f"{project_name}-{unique_id}"
        project_path = os.path.join(BASE_DIR, deployment_name)
        image_name = f"docker.io/{DOCKER_USERNAME}/mini-platform:{deployment_name}"

        yield f"Receiving zip file for {project_name}...\n"
        
        # Save zip file
        os.makedirs(project_path, exist_ok=True)
        zip_path = os.path.join(BASE_DIR, f"{deployment_name}.zip")
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        yield "Extracting zip file...\n"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(project_path)
            
        # Clean up the zip file
        os.remove(zip_path)

        yield "\nBuilding Docker image...\n"
        yield from stream_cmd(f"docker build -t {image_name} {project_path}")

        yield "\nPushing Docker image...\n"
        yield from stream_cmd(f"docker push {image_name}")

        yield "\nGenerating Kubernetes YAML...\n"

        yaml_content = generate_k8_yaml(deployment_name, image_name, DOMAIN)
        yaml_file = os.path.join(BASE_DIR, f"{deployment_name}.yaml")

        with open(yaml_file, "w") as f:
            f.write(yaml_content)

        yield "\nDeploying to Kubernetes...\n"
        yield from stream_cmd(f"kubectl apply -f {yaml_file}")

        yield "\n[SUCCESS] Deployment complete!\n"
        url = f"https://{deployment_name}.{DOMAIN}"
        save_deployment(deployment_name, url, "Zip Upload")
        yield f"[URL] {url}\n"
        yield f"[ID] {deployment_name}\n"

    return StreamingResponse(generator(), media_type="text/plain")

@app.get("/deployments")
def get_deployments():
    if os.path.exists(DEPLOYMENTS_FILE):
        with open(DEPLOYMENTS_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def run_redeploy(deployment_id: str):
    project_path = os.path.join(BASE_DIR, deployment_id)
    image_name = f"docker.io/{DOCKER_USERNAME}/mini-platform:{deployment_id}"
    
    if not os.path.exists(project_path):
        yield f"❌ Error: Project folder for {deployment_id} not found!\n"
        return
        
    yield f"Found existing codebase for {deployment_id}...\n"
    
    # Check if it's a git repo to pull changes
    if os.path.exists(os.path.join(project_path, ".git")):
        yield "Pulling latest changes from GitHub...\n"
        yield from stream_cmd(f"git -C {project_path} pull")

    yield "\nBuilding Docker image...\n"
    yield from stream_cmd(f"docker build -t {image_name} {project_path}")

    yield "\nPushing Docker image...\n"
    yield from stream_cmd(f"docker push {image_name}")

    yield "\nGenerating Kubernetes YAML...\n"
    yaml_content = generate_k8_yaml(deployment_id, image_name, DOMAIN)
    yaml_file = os.path.join(BASE_DIR, f"{deployment_id}.yaml")

    with open(yaml_file, "w") as f:
        f.write(yaml_content)

    yield "\nDeploying to Kubernetes...\n"
    yield from stream_cmd(f"kubectl apply -f {yaml_file}")

    yield "\n[SUCCESS] Redeployment complete!\n"
    url = f"https://{deployment_id}.{DOMAIN}"
    
    # update date
    save_deployment(deployment_id, url, "Auto-Webhook" if "webhook" in str(uuid.uuid4()) else "Redeploy")
    
    yield f"[URL] {url}\n"
    yield f"[ID] {deployment_id}\n"

@app.post("/redeploy/{deployment_id}")
def redeploy(deployment_id: str):
    return StreamingResponse(run_redeploy(deployment_id), media_type="text/plain")

@app.post("/webhook/{deployment_id}")
async def github_webhook(deployment_id: str, request: Request):
    # We could check for X-GitHub-Event: push here
    print(f"Received webhook for {deployment_id}")
    # Run redeploy in background or return streaming
    return StreamingResponse(run_redeploy(deployment_id), media_type="text/plain")

@app.delete("/projects/{deployment_id}")
def delete_deployment(deployment_id: str):
    import subprocess
    # Remove from JSON
    if os.path.exists(DEPLOYMENTS_FILE):
        with open(DEPLOYMENTS_FILE, "r") as f:
            try:
                deployments = json.load(f)
                new_deployments = [d for d in deployments if d["id"] != deployment_id]
                with open(DEPLOYMENTS_FILE, "w") as f:
                    json.dump(new_deployments, f, indent=4)
            except:
                pass

    # Clean up Kubernetes resources first
    yaml_file = os.path.join(BASE_DIR, f"{deployment_id}.yaml")
    if os.path.exists(yaml_file):
        subprocess.run(f"kubectl delete -f {yaml_file}", shell=True)
        os.remove(yaml_file)

    # Clean up local files
    project_path = os.path.join(BASE_DIR, deployment_id)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    
    return {"status": "deleted"}