document.getElementById("configForm").onsubmit = async (e)=>{
e.preventDefault()

const formData = new FormData()

document.querySelectorAll("#configForm input").forEach(input => {

if(input.type === "checkbox"){
formData.append(input.name, input.checked ? "true" : "false")
}else{
formData.append(input.name, input.value)
}

})

await fetch("/save_config",{
method:"POST",
body:formData
})

alert("Configuration saved")

}