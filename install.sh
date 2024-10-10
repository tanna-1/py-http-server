#!/usr/bin/env bash

if [ "$EUID" -ne 0 ]
    then echo "This script must be ran as root!"
    exit 1
fi

# Create http group and user
adduser --system --no-create-home --group http

# Create venv
mkdir /etc/py_http_server
cd /etc/py_http_server
apt install python3-venv
python3 -mvenv venv

# Install pip and py_http_server
venv/bin/python -mensurepip --upgrade
venv/bin/python -mpip install setuptools
venv/bin/python -mpip install git+https://github.com/tanna-1/py-http-server.git@master

# Create default config
cat << EOF > config.py
from py_http_server.middlewares import CompressMiddleware, DefaultMiddleware
from py_http_server.routers import FileRouter
from py_http_server.networking import TCPAddress
from py_http_server import app_main

app_main(
    handler_chain=DefaultMiddleware(CompressMiddleware(FileRouter("/var/www/html"))),
    http_listeners=[
        TCPAddress("127.0.0.1", 80),
        TCPAddress("::1", 80),
    ],
)
EOF
chmod +x config.py

# Create default document root
install -d -m 755 -o http -g http /var/www/html
chmod g+s /var/www/html
cat << EOF > /var/www/html/index.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome</title>
</head>
<body>
    Welcome!
</body>
</html>
EOF

# Check if the system uses systemd
if [ -d /run/systemd/system/ ]; then
    # Create the systemd service
    cat > /etc/systemd/system/py-http-server.service << EOF
[Unit]
Description=py-http-server
After=network.target
Wants=network.target

[Service]
Type=simple
User=http
Group=http
ExecStart=/etc/py_http_server/venv/bin/python /etc/py_http_server/config.py
AmbientCapabilities=CAP_NET_BIND_SERVICE
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    chmod 644 /etc/systemd/system/py-http-server.service

    # Enable and start the service
    systemctl daemon-reload
    systemctl enable py-http-server
    systemctl start py-http-server
else
    echo "Systemd not running or not available. Skipping service setup."
fi
