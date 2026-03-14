const logDiv = document.getElementById("log")
const cmdInput = document.getElementById("command")
const sendBtn = document.getElementById("sendCmd")

// refreshing logs every second
async function updateLogs(){
    try{
        const r = await fetch("/console_logs")
        const data = await r.json()
        if(data.logs.length){
            data.logs.forEach(line=>{
                const p = document.createElement("div")
                p.textContent = line
                logDiv.appendChild(p)
                logDiv.scrollTop = logDiv.scrollHeight
            })
        }
    }catch(e){}
    setTimeout(updateLogs, 1000)
}
updateLogs()

// send command
async function sendCommand() {
    const cmd = cmdInput.value.trim()
    if(!cmd) return

    await fetch("/console_command",{
        method:"POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({command: cmd})
    })

    cmdInput.value = ""
}

// bouton click (si présent)
if (sendBtn) {
    sendBtn.onclick = sendCommand
}

// appuyer sur Entrée
cmdInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        sendCommand()
    }
})