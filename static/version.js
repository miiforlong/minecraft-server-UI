const downloadBtn = document.getElementById("downloadBtn");
const versionInput = document.getElementById("version");
const statusDiv = document.getElementById("status");
const popup = document.getElementById("popup");
const confirmBtn = document.getElementById("confirmBtn");
const cancelBtn = document.getElementById("cancelBtn");
const uploadBtn = document.getElementById("uploadBtn");
const jarFile = document.getElementById("jarFile");

async function download(version, force=false) {
    try {
        statusDiv.textContent = "Downloading...";

        const response = await fetch("/download_version", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({version, force})
        });

        const data = await response.json();

        if (data.status === "exists") {
            popup.style.display = "flex";
            return;
        }

        if (data.status === "success") {
            statusDiv.textContent = "Download finished !";

            setTimeout(() => {
                alert("Téléchargement terminé !");
            }, 100);

            return;
        }

        statusDiv.textContent = "Error : " + data.message;
        alert("Erreur : " + data.message);

    } catch (err) {
        statusDiv.textContent = "Error : " + err;
        alert("Erreur réseau.");
    }
}

downloadBtn.addEventListener("click", () => {
    const version = versionInput.value.trim();
    if(version) download(version);
});

confirmBtn.addEventListener("click", () => {
    popup.style.display = "none";
    const version = versionInput.value.trim();
    if(version) download(version, true);
});

cancelBtn.addEventListener("click", () => {
    popup.style.display = "none";
    statusDiv.textContent = "Download cancelled.";
});


//upload custom jar

uploadBtn.addEventListener("click", async () => {

    if (!jarFile.files.length) {
        alert("Chose a .jar file");
        return;
    }

    const file = jarFile.files[0];

    if (!file.name.endsWith(".jar")) {
        alert("the file needs to be a .jar");
        return;
    }

    if (!confirm("Warning: This will delete your world and all its data. Continue?"))
        return;

    const formData = new FormData();
    formData.append("file", file);

    statusDiv.textContent = "Uploading jar...";

    try {
        const response = await fetch("/upload_jar", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.status === "success") {
            statusDiv.textContent = "";
            alert("Upload finished !");
        } else {
            statusDiv.textContent = "Error : " + data.message;
            alert("Erreur : " + data.message);
        }

    } catch (err) {
        statusDiv.textContent = "Error : " + err;
        alert("Network Error.");
    }

});