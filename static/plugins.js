async function downloadPlugin() {
    const url = document.getElementById("plugin_url").value;
    const res = await fetch("/plugins_download", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({url})
    });
    const data = await res.json();
    alert(data.status + (data.message ? ": "+data.message : ""));
    if(data.status==="success") location.reload();
}

async function uploadPlugin(event) {
    event.preventDefault();
    const form = document.getElementById("uploadForm");
    const formData = new FormData(form);
    const res = await fetch("/plugins_upload", {
        method: "POST",
        body: formData
    });
    const data = await res.json();
    alert(data.status + (data.message ? ": "+data.message : ""));
    if(data.status==="success") location.reload();
}

async function deletePlugin(name) {
    if(!confirm("Delete plugin "+name+"?")) return;
    const res = await fetch("/plugins_delete", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({plugin:name})
    });
    const data = await res.json();
    alert(data.status + (data.message ? ": "+data.message : ""));
    if(data.status==="success") location.reload();
}