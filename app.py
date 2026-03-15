from flask import Flask, render_template, jsonify, request
import subprocess
import os
import threading
import queue
import requests
import shutil
import json
import time
import psutil

app = Flask(__name__)

minecraft_process = None
server_path = "serveur"
eula_file = os.path.join(server_path, "eula.txt")
minecraft_logs = queue.Queue()
plugins_path = os.path.join(server_path, "plugins")
os.makedirs(plugins_path, exist_ok=True)

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
        try:
            minecraft_process = subprocess.Popen(
                ["java", "-Xmx2G", "-jar", "server.jar", "nogui"],
                cwd=server_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except FileNotFoundError:
            try:
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "openjdk-17-jdk"], check=True)

                minecraft_process = subprocess.Popen(
                    ["java", "-Xmx2G", "-jar", "server.jar", "nogui"],
                    cwd=server_path,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
            except Exception as e:
                return jsonify({"status":"error","message": f"Impossible d'installer Java : {e}"})

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
    players = []
    if not minecraft_process or minecraft_process.poll() is not None:
        return players
    try:
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
    ops = set()
    ops_file = os.path.join(server_path, "ops.json")
    if os.path.exists(ops_file):
        with open(ops_file) as f:
            data = json.load(f)
            ops = set([o["name"] for o in data])
    players = []
    usercache_file = os.path.join(server_path, "usercache.json")
    if os.path.exists(usercache_file):
        with open(usercache_file) as f:
            data = json.load(f)
            players = [entry["name"] for entry in data]
    return jsonify({"players": players, "ops": list(ops)})

@app.route("/plugins")
def plugins_page():
    plugins = []
    for f in os.listdir(plugins_path):
        if f.endswith(".jar"):
            plugin_dir = os.path.join(plugins_path, f.replace(".jar",""))
            config_exists = False
            config_file = None

            if os.path.isdir(plugin_dir):
                for item in os.listdir(plugin_dir):
                    if item.endswith(".yml"):
                        config_exists = True
                        config_file = os.path.join(plugin_dir, item)
                        break
            else:
                for item in os.listdir(plugins_path):
                    if item.endswith(".yml") and f[:-4].lower() in item.lower():
                        config_exists = True
                        config_file = os.path.join(plugins_path, item)
                        break

            plugins.append({
                "name": f,
                "config_exists": config_exists,
                "config_file": config_file
            })
    return render_template("plugins.html", plugins=plugins)

@app.route("/plugins_download", methods=["POST"])
def plugins_download():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"status":"error","message":"URL manquante"})
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        filename = url.split("/")[-1]
        if not filename.endswith(".jar"):
            return jsonify({"status":"error","message":"Fichier non .jar"})
        dest = os.path.join(plugins_path, filename)
        with open(dest,"wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","message": str(e)})

@app.route("/plugins_upload", methods=["POST"])
def plugins_upload():
    if "file" not in request.files:
        return jsonify({"status":"error","message":"Aucun fichier"})
    file = request.files["file"]
    if not file.filename.endswith(".jar"):
        return jsonify({"status":"error","message":"Fichier non .jar"})
    dest = os.path.join(plugins_path, file.filename)
    file.save(dest)
    return jsonify({"status":"success"})

@app.route("/plugins_config/<plugin_name>", methods=["GET","POST"])
def plugin_config(plugin_name):
    if ".." in plugin_name or not plugin_name.endswith(".jar"):
        return jsonify({"status":"error","message":"Plugin invalide"}),400
    config_file = os.path.join(plugins_path, plugin_name.replace(".jar",".yml"))
    if request.method == "POST":
        content = request.form.get("config", "")
        with open(config_file,"w") as f:
            f.write(content)
        return jsonify({"status":"saved"})
    else:
        content = ""
        if os.path.exists(config_file):
            with open(config_file) as f:
                content = f.read()
        return render_template("plugin_config.html", plugin=plugin_name, config=content)

@app.route("/plugins_delete", methods=["POST"])
def plugins_delete():
    plugin_name = request.json.get("plugin")
    if not plugin_name:
        return jsonify({"status":"error","message":"Plugin manquant"})
    plugin_file = os.path.join(plugins_path, plugin_name)
    plugin_dir = os.path.join(plugins_path, plugin_name.replace(".jar",""))
    try:
        if os.path.exists(plugin_file):
            os.remove(plugin_file)
        if os.path.isdir(plugin_dir):
            shutil.rmtree(plugin_dir)
        for item in os.listdir(plugins_path):
            if item.endswith(".yml") and plugin_name[:-4].lower() in item.lower():
                os.remove(os.path.join(plugins_path, item))
        return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","message": str(e)})

def get_system_stats():
    process = psutil.Process(os.getpid())
    cpu_script = process.cpu_percent(interval=0.2)

    ram = psutil.virtual_memory()

    cpu_temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                for entry in entries:
                    cpu_temp = entry.current
                    break
                if cpu_temp:
                    break
    except:
        pass

    if cpu_temp is None:
        thermal = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(thermal):
            with open(thermal) as f:
                cpu_temp = round(int(f.read())/1000,1)

    return {
        "cpu_temp": cpu_temp,
        "cpu_script_percent": cpu_script,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used/(1024**3),2),
        "ram_total_gb": round(ram.total/(1024**3),2)
    }

@app.route("/system_stats")
def system_stats():
    return jsonify(get_system_stats())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)