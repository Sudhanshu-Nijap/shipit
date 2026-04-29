let currentMode = 'github';
let currentDeploymentId = null; // Track the most recent deployment ID

function setMode(mode) {
    currentMode = mode;
    
    // Update tabs
    document.getElementById('tab-github').classList.remove('active');
    document.getElementById('tab-zip').classList.remove('active');
    document.getElementById(`tab-${mode}`).classList.add('active');
    
    // Update inputs
    const githubInput = document.getElementById('github-input-wrapper');
    const zipInput = document.getElementById('zip-input-wrapper');
    
    if (mode === 'github') {
        githubInput.classList.remove('hidden');
        zipInput.classList.add('hidden');
    } else {
        githubInput.classList.add('hidden');
        zipInput.classList.remove('hidden');
    }
}

async function deploy() {
    const repo = document.getElementById("repo").value;
    const zipfile = document.getElementById("zipfile").files[0];
    const name = document.getElementById("name").value;
    const logs = document.getElementById("logs");
    const successPanel = document.getElementById("successPanel");
    const liveUrl = document.getElementById("liveUrl");
    const statusBadge = document.getElementById("statusBadge");

    const btn = document.getElementById("deployBtn");
    const btnText = document.getElementById("btnText");
    const btnIcon = document.getElementById("btnIcon");

    if (!name) {
        alert("Project Name is required!");
        return;
    }

    if (currentMode === 'github' && !repo) {
        alert("GitHub URL is required!");
        return;
    }

    if (currentMode === 'zip' && !zipfile) {
        alert("Please upload a .zip file!");
        return;
    }

    logs.innerText = "";
    successPanel.classList.add("hidden");

    // 🔵 Button state
    btn.disabled = true;
    btn.classList.add("deploying");
    btnIcon.className = "fa-solid fa-spinner fa-spin";
    btnText.innerText = "Deploying";

    // 🔵 Badge state
    statusBadge.innerText = "Deploying";
    statusBadge.className = "badge deploying";

    let response;
    
    if (currentMode === 'github') {
        response = await fetch("/deploy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ github_url: repo, project_name: name })
        });
    } else {
        const formData = new FormData();
        formData.append("project_name", name);
        formData.append("file", zipfile);
        
        response = await fetch("/deploy-zip", {
            method: "POST",
            body: formData
        });
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let finalUrl = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        logs.innerText += chunk;
        logs.scrollTop = logs.scrollHeight;

        if (chunk.includes("Building Docker")) {
            statusBadge.innerText = "Building";
        }

        if (chunk.includes("Deploying to Kubernetes")) {
            statusBadge.innerText = "Deploying";
        }

        if (chunk.includes("[URL]")) {
            finalUrl = chunk.split("[URL]")[1].trim();
        }

        if (chunk.includes("[ID]")) {
            currentDeploymentId = chunk.split("[ID]")[1].trim();
        }
    }


    // 🔵 Reset button
    btn.disabled = false;
    btn.classList.remove("deploying");
    btnIcon.className = "fa-solid fa-rocket";
    btnText.innerText = "Deploy";

    if (finalUrl) {
        statusBadge.innerText = "Live";
        statusBadge.className = "badge success";

        liveUrl.innerText = finalUrl;
        liveUrl.href = finalUrl;
        successPanel.classList.remove("hidden");
        
        // Save the actual deployment ID for redeployment
        // The ID is prefix-suffix.
        // We can extract it from the URL or just rely on the name variable if we make it global.
        
        // Show Webhook info
        showWebhook(currentDeploymentId);
        
        loadDeployments();
    }
}

function redeployCurrent() {
    if (currentDeploymentId) {
        redeploy(currentDeploymentId);
    }
}

function showWebhook(deploymentId) {
    const webhookSection = document.getElementById("webhookSection");
    const webhookUrl = document.getElementById("webhookUrl");
    if (!webhookSection || !webhookUrl) return;

    const url = `${window.location.origin}/webhook/${deploymentId}`;
    webhookUrl.innerText = url;
    webhookSection.classList.remove("hidden");
}

function copyWebhook() {
    const text = document.getElementById("webhookUrl").innerText;
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector(".copy-icon-btn i");
        btn.className = "fa-solid fa-check";
        setTimeout(() => {
            btn.className = "fa-solid fa-copy";
        }, 1500);
    });
}

function copyUrl() {
    const text = document.getElementById("liveUrl").innerText;
    const copyText = document.getElementById("copyText");
    const copyBtn = document.getElementById("copyBtn");

    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        copyText.innerText = "Copied!";
        copyBtn.classList.add("copied");

        setTimeout(() => {
            copyText.innerText = "Copy";
            copyBtn.classList.remove("copied");
        }, 1500);
    });
}

function fallbackCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    showCopySuccess();
}

async function loadDeployments() {
    const list = document.getElementById("deploymentsList");
    if (!list) return;
    try {
        const response = await fetch("/deployments");
        const data = await response.json();
        
        if (!data || data.length === 0) {
            list.innerHTML = '<div class="project-empty"><i class="fa-solid fa-folder-open"></i><p>No deployments yet. Deploy your first project above!</p></div>';
            return;
        }
        
        list.innerHTML = data.map(dep => `
            <div class="project-item-card">
                <div class="project-info-main">
                    <div class="project-name-wrapper">
                        <span class="project-name">${dep.name}</span>
                        <span class="badge" style="background: transparent; color: var(--text-secondary); border-color: var(--border-color); font-size: 10px;">${dep.type}</span>
                    </div>
                    <a href="${dep.url}" target="_blank" class="project-url">${dep.url.replace('https://', '')}</a>
                    <div class="project-meta">
                        <span><i class="fa-regular fa-calendar"></i> ${dep.date}</span>
                        <span style="color: var(--success); font-weight: 600; display: flex; align-items: center; gap: 4px;">
                            <i class="fa-solid fa-circle" style="font-size: 6px;"></i> Ready
                        </span>
                    </div>
                </div>
                <div class="project-actions">
                    <button class="action-btn" onclick="redeploy('${dep.id}')" title="Redeploy">
                        <i class="fa-solid fa-rotate"></i>
                    </button>
                    <button class="action-btn" onclick="deleteProject('${dep.id}')" style="border-color: rgba(239, 68, 68, 0.2); color: #ef4444;" title="Delete">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        list.innerHTML = '<tr><td colspan="5" class="empty-state">Failed to load deployments.</td></tr>';
    }
}

async function redeploy(id) {
    const logs = document.getElementById("logs");
    const successPanel = document.getElementById("successPanel");
    const liveUrl = document.getElementById("liveUrl");
    const statusBadge = document.getElementById("statusBadge");

    logs.innerText = `Starting redeployment for ${id}...\n`;
    successPanel.classList.add("hidden");
    statusBadge.innerText = "Deploying";
    statusBadge.className = "badge deploying";

    // Scroll to console
    const consoleCard = document.getElementById("redeployConsole");
    if (consoleCard) {
        consoleCard.classList.remove("hidden");
        consoleCard.scrollIntoView({ behavior: 'smooth' });
    }

    try {
        const response = await fetch(`/redeploy/${id}`, { method: "POST" });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let finalUrl = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            logs.innerText += chunk;
            logs.scrollTop = logs.scrollHeight;

            if (chunk.includes("Building Docker")) statusBadge.innerText = "Building";
            if (chunk.includes("Deploying to Kubernetes")) statusBadge.innerText = "Deploying";
            if (chunk.includes("[URL]")) finalUrl = chunk.split("[URL]")[1].trim();
            if (chunk.includes("[ID]")) currentDeploymentId = chunk.split("[ID]")[1].trim();
        }

        if (finalUrl) {
            statusBadge.innerText = "Live";
            statusBadge.className = "badge success";
            liveUrl.innerText = finalUrl;
            liveUrl.href = finalUrl;
            successPanel.classList.remove("hidden");
            
            // Show Webhook info
            showWebhook(id);
            
            // Refresh list to update timestamp
            loadDeployments();
        } else {
            statusBadge.innerText = "Failed";
            statusBadge.className = "badge idle";
        }
    } catch (e) {
        logs.innerText += `\nError: ${e.message}`;
        statusBadge.innerText = "Error";
        statusBadge.className = "badge idle";
    }
}

async function deleteProject(id) {
    if (!confirm(`Are you sure you want to delete ${id}? This will remove all files and the Kubernetes deployment.`)) {
        return;
    }

    try {
        const response = await fetch(`/projects/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadDeployments();
        } else {
            alert("Failed to delete project.");
        }
    } catch (err) {
        alert("Error deleting project.");
    }
}

// Load on start
window.addEventListener('DOMContentLoaded', loadDeployments);

function showCopySuccess() {
    const btn = document.querySelector(".result-url button");
    btn.innerText = "Copied!";
    setTimeout(() => {
        btn.innerText = "Copy";
    }, 1500);
}