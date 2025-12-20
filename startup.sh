#!/bin/bash
set -e

echo "===== FastAPI startup script started ====="

# -------- CONFIG --------
APP_DIR="/opt/fastapi"
APP_USER="ubuntu"
PORT=8000
PYTHON_BIN="/usr/bin/python3"

# -------- SYSTEM UPDATE --------
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git

# -------- CREATE APP DIRECTORY --------
mkdir -p $APP_DIR
chown -R $APP_USER:$APP_USER $APP_DIR

# -------- SWITCH TO APP USER --------
sudo -u $APP_USER bash <<EOF

cd $APP_DIR

# -------- OPTIONAL: CLONE FROM GIT --------
git clone https://github.com/winssoftdev-spec/Demo_api.git .

# -------- CREATE VENV --------
$PYTHON_BIN -m venv venv
source venv/bin/activate

# -------- INSTALL DEPENDENCIES --------
pip install --upgrade pip
pip install fastapi uvicorn gunicorn

EOF

# -------- SYSTEMD SERVICE --------
cat > /etc/systemd/system/fastapi.service <<SERVICE
[Unit]
Description=FastAPI ERP Service
After=network.target

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --workers 3
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

# -------- ENABLE & START SERVICE --------
systemctl daemon-reload
systemctl enable fastapi
systemctl restart fastapi

echo "===== FastAPI startup script completed ====="