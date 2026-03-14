document.getElementById("startserver").addEventListener("click", () => {
    fetch("/start", {
        method: "POST"
    })
    .then(response => response.text())
    .then(data => console.log(data));
});