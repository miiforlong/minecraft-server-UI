# Minecraft Server UI

Notes: 
- Some features will not be available with older versions of Minecraft (such as the "Players" tab). Minecraft 1.8 is provided as an example for testing purposes, but for optimal use, it is recommended to install a more recent version.
- Minecraft Server UI was designed for Linux. Therefore, it may not work optimally on Windows.

________________________________

requirements : 

- last version Python
- flask (python requirement)
- psutil (python requirement)
- java
  

Requirements installation (linux only) : 

#### update
```bash
sudo apt update
```

#### install python, pip, venv and java 21 (install the java that matches your minecraft version)
```bash
sudo apt install -y python3 python3-pip python3-venv openjdk-21-jdk
```

#### install the python requirements
```bash
python3 -m pip install -r requirements.txt --break-system-packages
```

_________________________________

How to set up (linux only) : 

- put all the files in a folder in your server :

#### update
```bash
sudo apt update
```

#### install git
```bash
sudo apt install git -y
```

#### clone the repo
```bash
git clone https://github.com/miiforlong/minecraft-server-UI.git
```

#### go in the folder
```bash
cd minecraft-server-UI
```

- start the server :
  
```bash
python3 app.py
```

- go the the web interface it indicates you (by default : "serverip:5000", you can change this at the end of app.py, just replace "5000" by the port of your choice)

<img width="571" height="137" alt="image" src="https://github.com/user-attachments/assets/e26a996f-4c68-4f97-b30c-bcb5296fe057" />
  
- if you wanna put a password edit "pswd.txt" from "Null" to any password so you can put it online securely
