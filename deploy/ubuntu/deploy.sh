#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/taiko-ratingpro}
APP_USER=${APP_USER:-$USER}
PYTHON=${PYTHON:-python3}

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

$SUDO apt-get update
$SUDO apt-get install -y nginx nodejs npm python3-venv

cd "$APP_DIR"

$PYTHON -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[web]"

cd webui
npm install
npm run build
cd ..

$SUDO cp deploy/ubuntu/taiko-rating.service /etc/systemd/system/taiko-rating.service
$SUDO sed -i "s|__APP_DIR__|$APP_DIR|g" /etc/systemd/system/taiko-rating.service
$SUDO sed -i "s|__APP_USER__|$APP_USER|g" /etc/systemd/system/taiko-rating.service

$SUDO cp deploy/ubuntu/nginx-taiko-rating.conf /etc/nginx/sites-available/taiko-rating
$SUDO sed -i "s|/opt/taiko-ratingpro|$APP_DIR|g" /etc/nginx/sites-available/taiko-rating
$SUDO mkdir -p /etc/nginx/snippets
$SUDO cp deploy/ubuntu/nginx-api-allowlist.conf /etc/nginx/snippets/taiko-rating-api-allowlist.conf
$SUDO ln -sf /etc/nginx/sites-available/taiko-rating /etc/nginx/sites-enabled/taiko-rating
$SUDO rm -f /etc/nginx/sites-enabled/default

$SUDO systemctl daemon-reload
$SUDO systemctl enable taiko-rating
$SUDO systemctl restart taiko-rating
$SUDO nginx -t
$SUDO systemctl restart nginx

echo "Deployment complete. Open: http://<your-server-ip>/"
