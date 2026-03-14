const btn = document.getElementById("startserver")
const popup = document.getElementById("eulaPopup")
const acceptBtn = document.getElementById("acceptEula")

let running = false

// au chargement de la page check si le serveur est allumé ou éteint pour afficher "start" ou "stop" the server
async function syncStatus(){
    const r = await fetch("/status")
    const data = await r.json()

    running = data.running
    btn.textContent = running ? "Stop the server" : "Start the server"
}

syncStatus()

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