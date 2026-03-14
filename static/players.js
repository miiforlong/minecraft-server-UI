        const gamemodes = ["survival","creative","adventure","spectator"];

        async function refreshPlayers(){
            const res = await fetch("/players_data");
            const data = await res.json();
            const tbody = document.querySelector("table tbody");
            tbody.innerHTML = ""; // clear old rows

            data.players.forEach(player => {
                const tr = document.createElement("tr");

                // Player name
                const tdName = document.createElement("td");
                tdName.textContent = player;
                tr.appendChild(tdName);

                // OP checkbox
                const tdOp = document.createElement("td");
                const cb = document.createElement("input");
                cb.type = "checkbox";
                cb.checked = data.ops.includes(player);
                cb.addEventListener("change", async ()=> {
                    const op = cb.checked;
                    const res = await fetch("/players_op", {
                        method:"POST",
                        headers: {"Content-Type":"application/json"},
                        body: JSON.stringify({player, op})
                    });
                    const resp = await res.json();
                    if(resp.status!=="ok"){
                        alert("OP/DEOP Error: "+resp.message);
                        cb.checked = !op;
                    }
                });
                tdOp.appendChild(cb);
                tr.appendChild(tdOp);

                // Actions Ban / Unban
                const tdAction = document.createElement("td");
                const btnBan = document.createElement("button");
                btnBan.textContent = "Ban";
                btnBan.addEventListener("click", async ()=> {
                    if(!confirm("Are you sure you want to ban this player?")) return;
                    const res = await fetch("/players_ban", {
                        method:"POST",
                        headers: {"Content-Type":"application/json"},
                        body: JSON.stringify({player})
                    });
                    const resp = await res.json();
                    if(resp.status==="ok"){
                        alert(player+" has been banned!");
                        refreshPlayers();
                    } else {
                        alert("Error: "+resp.message);
                    }
                });
                tdAction.appendChild(btnBan);

                const btnUnban = document.createElement("button");
                btnUnban.textContent = "Unban";
                btnUnban.addEventListener("click", async ()=> {
                    if(!confirm("Are you sure you want to unban this player?")) return;
                    const res = await fetch("/players_unban", {
                        method:"POST",
                        headers: {"Content-Type":"application/json"},
                        body: JSON.stringify({player})
                    });
                    const resp = await res.json();
                    if(resp.status==="ok"){
                        alert(player+" has been unbanned!");
                        refreshPlayers();
                    } else {
                        alert("Error: "+resp.message);
                    }
                });
                tdAction.appendChild(btnUnban);
                tr.appendChild(tdAction);

                // Gamemode
                const tdGamemode = document.createElement("td");
                const select = document.createElement("select");
                gamemodes.forEach(mode => {
                    const option = document.createElement("option");
                    option.value = mode;
                    option.textContent = mode;
                    select.appendChild(option);
                });
                select.addEventListener("change", async ()=> {
                    const mode = select.value;
                    const res = await fetch("/players_gamemode", {
                        method:"POST",
                        headers: {"Content-Type":"application/json"},
                        body: JSON.stringify({player, gamemode: mode})
                    });
                    const resp = await res.json();
                    if(resp.status==="ok"){
                        alert(player+" is now in "+mode+" mode");
                    } else {
                        alert("Error: "+resp.message);
                    }
                });
                tdGamemode.appendChild(select);
                tr.appendChild(tdGamemode);

                tbody.appendChild(tr);
            });
        }

        refreshPlayers();
        setInterval(refreshPlayers, 20000);