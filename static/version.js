const versionsGrid = document.getElementById("versionsGrid");
const loading = document.getElementById("loading");
const errorContainer = document.getElementById("errorContainer");
const statusDiv = document.getElementById("status");
const popup = document.getElementById("popup");
const confirmBtn = document.getElementById("confirmBtn");
const cancelBtn = document.getElementById("cancelBtn");
const uploadBtn = document.getElementById("uploadBtn");
const jarFile = document.getElementById("jarFile");

let selectedVersion = null;

// Load available versions when the page is ready
document.addEventListener("DOMContentLoaded", loadVersions);

async function loadVersions() {
    try {
        loading.style.display = "block";
        versionsGrid.innerHTML = "";
        errorContainer.innerHTML = "";

        const response = await fetch("/get_versions");
        const data = await response.json();

        if (data.status !== "success") {
            throw new Error(data.message || "Error while loading versions");
        }

        const versions = data.versions || [];
        loading.style.display = "none";

        if (versions.length === 0) {
            errorContainer.innerHTML = "<div class='error-message'>No versions available</div>";
            return;
        }

        // Display available versions
        versions.forEach(version => {
            const versionBlock = document.createElement("div");
            versionBlock.className = "version-block";
            versionBlock.innerHTML = `
                <div class="version-number">${version}</div>
                <div class="version-label">PaperMC</div>
            `;

            versionBlock.addEventListener("click", () => selectVersion(version));
            versionsGrid.appendChild(versionBlock);
        });

        // Add the custom JAR upload block
        const uploadBlock = document.createElement("div");
        uploadBlock.className = "version-block";
        uploadBlock.id = "uploadJarBlock";
        uploadBlock.innerHTML = `
            <div class="upload-icon"></div>
            <div class="version-label">📤 Import Custom JAR</div>
        `;

        uploadBlock.addEventListener("click", triggerFileInput);
        versionsGrid.appendChild(uploadBlock);

    } catch (err) {
        loading.style.display = "none";
        errorContainer.innerHTML = `<div class='error-message'>Error: ${err.message}</div>`;
        console.error("Error:", err);
    }
}

function selectVersion(version) {
    selectedVersion = version;
    popup.style.display = "flex";
}

confirmBtn.addEventListener("click", () => {
    popup.style.display = "none";

    if (selectedVersion) {
        downloadVersion(selectedVersion, true);
    }
});

cancelBtn.addEventListener("click", () => {
    popup.style.display = "none";
    selectedVersion = null;
    showStatus("Download cancelled.", "info");
});

async function downloadVersion(version, force = false) {
    try {
        statusDiv.className = "";
        statusDiv.textContent = "Download in progress...";

        const response = await fetch("/download_version", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                version,
                force
            })
        });

        const data = await response.json();

        if (data.status === "exists") {
            popup.style.display = "flex";
            return;
        }

        if (data.status === "success") {
            showStatus("Download completed!", "success");
            selectedVersion = null;

            setTimeout(() => {
                alert("Version " + version + " downloaded successfully!");
            }, 500);

            return;
        }

        showStatus("Error: " + data.message, "error");
        alert("Error: " + data.message);

    } catch (err) {
        showStatus("Network error", "error");
        alert("Network error: " + err.message);
    }
}

function triggerFileInput() {
    jarFile.click();
}

jarFile.addEventListener("change", async (e) => {
    const file = e.target.files[0];

    if (!file) {
        return;
    }

    if (!file.name.endsWith(".jar")) {
        showStatus("The file must be a .jar file", "error");
        alert("The file must be a .jar file");
        return;
    }

    if (!confirm(
        "Warning:\n" +
        "This will delete all your configuration files and your world!\n\n" +
        "Continue?"
    )) {
        jarFile.value = "";
        return;
    }

    uploadJar(file);
});

async function uploadJar(file) {
    try {
        statusDiv.className = "";
        statusDiv.textContent = "Uploading JAR file...";

        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/upload_jar", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.status === "success") {
            showStatus("Upload completed!", "success");
            jarFile.value = "";
            alert("JAR file uploaded successfully!");
        } else {
            showStatus("Error: " + data.message, "error");
            alert("Error: " + data.message);
        }

    } catch (err) {
        showStatus("Network error", "error");
        alert("Network error: " + err.message);
    }
}

function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = type;

    if (type === "success") {
        setTimeout(() => {
            statusDiv.textContent = "";
            statusDiv.className = "";
        }, 3000);
    }
}