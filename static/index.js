const btn = document.getElementById("startserver")
const popup = document.getElementById("eulaPopup")
const acceptBtn = document.getElementById("acceptEula")

const cpuUsage = document.getElementById("cpu_usage")
const cpuTemp = document.getElementById("cpu_temp")
const ramPercent = document.getElementById("ram_percent")
const ramUsed = document.getElementById("ram_used")
const ramTotal = document.getElementById("ram_total")

let running = false

async function syncStatus(){
    const r = await fetch("/status")
    const data = await r.json()

    running = data.running
    btn.textContent = running ? "Stop the server" : "Start the server"
}

syncStatus()

async function updateStats(){
    const r = await fetch("/system_stats")
    const data = await r.json()

    cpuUsage.textContent = data.cpu_script_percent.toFixed(1)
    cpuTemp.textContent = data.cpu_temp.toFixed(1)

    ramPercent.textContent = data.ram_percent.toFixed(1)
    ramUsed.textContent = data.ram_used_gb.toFixed(2)
    ramTotal.textContent = data.ram_total_gb.toFixed(2)
}

setInterval(updateStats, 2000)
updateStats()

btn.onclick = async () => {

    if(!running){

        const r = await fetch("/start", {method:"POST"})
        const data = await r.json()

        if(!data.eula){
            popup.style.display = "block"
            return
        }

        btn.textContent = "Stop the server"
        running = true
    }
    else{

        await fetch("/stop", {method:"POST"})

        btn.textContent = "Start the server"
        running = false
    }
}

acceptBtn.onclick = async () => {

    await fetch("/accept_eula", {method:"POST"})

    popup.style.display = "none"

    btn.textContent = "Stop the server"
    running = true
}