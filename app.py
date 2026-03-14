from flask import Flask, render_template
import subprocess

app = Flask(__name__)

minecraft_process = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_server():
    global minecraft_process

    if minecraft_process is None:
        minecraft_process = subprocess.Popen(
            ["java", "-Xmx2G", "-jar", "server.jar", "nogui"],
            cwd="serveur"
        )
        return "Serveur démarré"

    return "Déjà lancé"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)