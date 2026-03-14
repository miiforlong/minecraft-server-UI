from flask import Flask, render_template, jsonify, request
import subprocess
import os
import threading
import queue
import requests
import shutil
import json
import time

app = Flask(__name__)

minecraft_process = None
server_path = "serveur"
eula_file = os.path.join(server_path, "eula.txt")
minecraft_logs = queue.Queue()

def eula_accepted():
    if not os.path.exists(eula_file):
        return False
    with open(eula_file) as f:
        return "eula=true" in f.read()

def read_stdout(proc):
    """Lit stdout du serveur et stocke les lignes dans une queue."""
    for line in proc.stdout:
        minecraft_logs.put(line.strip())

@app.route("/")
def index():
    return render_template("index.html", eula=eula_accepted())

@app.route("/start", methods=["POST"])
def start_server():
    global minecraft_process
    if not eula_accepted():
        return jsonify({"eula": False})

    if minecraft_process is None or minecraft_process.poll() is not None:
        minecraft_process = subprocess.Popen(
            ["java", "-Xmx2G", "-jar", "server.jar", "nogui"],
            cwd=server_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        threading.Thread(target=read_stdout, args=(minecraft_process,), daemon=True).start()

    return jsonify({"eula": True})

@app.route("/stop", methods=["POST"])
def stop_server():
    global minecraft_process
    if minecraft_process and minecraft_process.poll() is None:
        minecraft_process.stdin.write("stop\n")
        minecraft_process.stdin.flush()
        return jsonify({"status": "stopping"})
    return jsonify({"status": "not_running"})

@app.route("/accept_eula", methods=["POST"])
def accept_eula():
    os.makedirs(server_path, exist_ok=True)
    with open(eula_file, "w") as f:
        f.write("eula=true\n")
    return start_server()

@app.route("/config")
def config():
    props = {}
    props_file = os.path.join(server_path, "server.properties")
    if os.path.exists(props_file):
        with open(props_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=",1)
                    props[key] = value
    return render_template("config.html", props=props)

@app.route("/save_config", methods=["POST"])
def save_config():
    props_file = os.path.join(server_path, "server.properties")
    with open(props_file, "w") as f:
        for key,value in request.form.items():
            f.write(f"{key}={value}\n")
    return jsonify({"saved":True})

@app.route("/status")
def server_status():
    global minecraft_process
    running = minecraft_process is not None and minecraft_process.poll() is None
    return jsonify({"running": running})

@app.route("/console")
def console_page():
    return render_template("console.html")

@app.route("/console_logs")
def console_logs():
    logs = []
    while not minecraft_logs.empty():
        logs.append(minecraft_logs.get())
    return jsonify({"logs": logs})

@app.route("/console_command", methods=["POST"])
def console_command():
    global minecraft_process
    cmd = request.json.get("command", "")
    if minecraft_process and minecraft_process.poll() is None and cmd:
        minecraft_process.stdin.write(cmd + "\n")
        minecraft_process.stdin.flush()
        return jsonify({"status": "sent"})
    return jsonify({"status": "error"})

@app.route("/version")
def version_page():
    return render_template("version.html")

@app.route("/download_version", methods=["POST"])
def download_version():
    data = request.json
    version = data.get("version")
    force = data.get("force", False)
    if not version:
        return jsonify({"status": "error", "message": "Version manquante"})

    if os.path.exists(server_path) and os.listdir(server_path) and not force:
        return jsonify({"status": "exists", "message": "Attention, cela va supprimer votre monde et toutes ses données"})

    if os.path.exists(server_path):
        shutil.rmtree(server_path)
    os.makedirs(server_path, exist_ok=True)

    try:
        api_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}"
        res = requests.get(api_url)
        res.raise_for_status()
        builds = res.json().get("builds", [])
        if not builds:
            return jsonify({"status": "error", "message": "Version invalide"})
        latest_build = max(builds)
        jar_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{latest_build}/downloads/paper-{version}-{latest_build}.jar"

        jar_path = os.path.join(server_path, "server.jar")
        r = requests.get(jar_url, stream=True)
        r.raise_for_status()
        with open(jar_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/upload_jar", methods=["POST"])
def upload_jar():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "Aucun fichier"})

    file = request.files["file"]
    if file.filename == "" or not file.filename.endswith(".jar"):
        return jsonify({"status": "error", "message": "Fichier invalide ou non .jar"})

    if os.path.exists(server_path):
        shutil.rmtree(server_path)
    os.makedirs(server_path, exist_ok=True)

    jar_path = os.path.join(server_path, "server.jar")
    file.save(jar_path)

    return jsonify({"status": "success"})

@app.route("/players")
def players_page():
    return render_template("players.html")

@app.route("/players_op", methods=["POST"])
def player_op():
    player = request.json.get("player")
    op = request.json.get("op", False)
    if not player:
        return jsonify({"status":"error","message":"No player"})
    if minecraft_process is None or minecraft_process.poll() is not None:
        return jsonify({"status":"error","message":"Server not running"})
    cmd = f"op {player}" if op else f"deop {player}"
    minecraft_process.stdin.write(cmd+"\n")
    minecraft_process.stdin.flush()
    return jsonify({"status":"ok"})

@app.route("/players_ban", methods=["POST"])
def player_ban():
    player = request.json.get("player")
    if not player:
        return jsonify({"status":"error","message":"No player"})
    if minecraft_process is None or minecraft_process.poll() is not None:
        return jsonify({"status":"error","message":"Server not running"})
    minecraft_process.stdin.write(f"ban {player}\n")
    minecraft_process.stdin.flush()
    return jsonify({"status":"ok"})

@app.route("/players_gamemode", methods=["POST"])
def player_gamemode():
    player = request.json.get("player")
    gamemode = request.json.get("gamemode")
    if not player or gamemode not in ["survival","creative","adventure","spectator"]:
        return jsonify({"status":"error","message":"Player missing or invalid gamemode"})
    if minecraft_process is None or minecraft_process.poll() is not None:
        return jsonify({"status":"error","message":"Server not running"})
    # envoie la commande /gamemode <mode> <joueur>
    minecraft_process.stdin.write(f"gamemode {gamemode} {player}\n")
    minecraft_process.stdin.flush()
    return jsonify({"status":"ok"})

@app.route("/players_unban", methods=["POST"])
def player_unban():
    player = request.json.get("player")
    if not player:
        return jsonify({"status":"error","message":"No player"})
    if minecraft_process is None or minecraft_process.poll() is not None:
        return jsonify({"status":"error","message":"Server not running"})
    minecraft_process.stdin.write(f"pardon {player}\n")
    minecraft_process.stdin.flush()
    return jsonify({"status":"ok"})

def get_connected_players():
    """Récupère les joueurs actuellement connectés via la commande 'list'."""
    players = []
    if not minecraft_process or minecraft_process.poll() is not None:
        return players
    try:
        # envoyer 'list'
        minecraft_process.stdin.write("list\n")
        minecraft_process.stdin.flush()
        start_time = time.time()
        while time.time() - start_time < 1.0:
            while not minecraft_logs.empty():
                line = minecraft_logs.get()
                if "There are" in line and ":" in line:
                    names = line.split(":")[-1].strip()
                    players = [n.strip() for n in names.split(",") if n.strip()]
                    return players
            time.sleep(0.05)
    except Exception as e:
        print("Erreur get_connected_players:", e)
    return players

@app.route("/players_data")
def players_data():
    """Retourne tous les joueurs déjà connectés et les ops actuels."""
    # OPS
    ops = set()
    ops_file = os.path.join(server_path, "ops.json")
    if os.path.exists(ops_file):
        with open(ops_file) as f:
            data = json.load(f)
            ops = set([o["name"] for o in data])

    # Joueurs connus
    players = []
    usercache_file = os.path.join(server_path, "usercache.json")
    if os.path.exists(usercache_file):
        with open(usercache_file) as f:
            data = json.load(f)
            players = [entry["name"] for entry in data]

    return jsonify({"players": players, "ops": list(ops)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)