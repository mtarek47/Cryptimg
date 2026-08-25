# Stegstr — Production Deployment Guidelines

Complete production deployment guide for running **Stegstr** API server, Web UI Dashboard, and Nostr Relay Manager across Docker, VPS (Ubuntu/Debian), Nginx SSL reverse proxy, and Cloud platforms.

---

## 1. Quick Start with Docker Compose (Recommended)

The fastest and most reliable way to deploy Stegstr in production is using Docker Compose.

### Step 1: Clone Repository & Create Data Directory
```bash
git clone https://github.com/your-org/stegstr.git
cd stegstr
mkdir -p data
```

### Step 2: Build & Start Service
```bash
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
# Check container status
docker compose ps

# Inspect live application logs
docker compose logs -f

# Run internal health check
curl http://127.0.0.1:8765/api/v1/status
```

---

## 2. Bare-Metal / VPS Systemd Deployment (Linux / Ubuntu)

For deploying directly on an Ubuntu/Debian Linux VPS (DigitalOcean, Linode, AWS EC2, Hetzner):

### Step 1: Install System Dependencies
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git libjpeg-dev zlib1g-dev
```

### Step 2: Setup Application Directory & Virtual Environment
```bash
sudo useradd -m -s /bin/bash stegstr
sudo mkdir -p /opt/stegstr /var/lib/stegstr/data
sudo chown -R stegstr:stegstr /opt/stegstr /var/lib/stegstr

sudo -u stegstr git clone https://github.com/your-org/stegstr.git /opt/stegstr
cd /opt/stegstr

sudo -u stegstr python3 -m venv venv
sudo -u stegstr ./venv/bin/pip install --no-cache-dir numpy pillow ecdsa fastapi uvicorn pydantic python-multipart
```

### Step 3: Create Systemd Service Unit
Create file `/etc/systemd/system/stegstr.service`:

```ini
[Unit]
Description=Stegstr API Server & Web UI Engine
After=network.target

[Service]
Type=simple
User=stegstr
Group=stegstr
WorkingDirectory=/opt/stegstr
Environment="STEGSTR_DATA_DIR=/var/lib/stegstr/data"
ExecStart=/opt/stegstr/venv/bin/python3 -m stegstr.api.server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 4: Enable & Start Systemd Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable stegstr
sudo systemctl start stegstr
sudo systemctl status stegstr
```

---

## 3. Nginx Reverse Proxy & SSL (HTTPS / WSS) Setup

To expose Stegstr securely over domain `stegstr.yourdomain.com` with Let's Encrypt SSL:

### Step 1: Install Nginx & Certbot
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Step 2: Configure Nginx Virtual Host
Create `/etc/nginx/sites-available/stegstr`:

```nginx
server {
    server_name stegstr.yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable domain and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/stegstr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 3: Issue Free SSL Certificate
```bash
sudo certbot --nginx -d stegstr.yourdomain.com
```

Now access your live production dashboard at `https://stegstr.yourdomain.com/app`!

---

## 4. Production Security & Optimization Guidelines

1. **Persistent Data Volume**: Ensure `/var/lib/stegstr/data` or Docker volume `./data` is backed up regularly (`stegstr.db` stores active keys & offline queue).
2. **File Size Limits**: Nginx `client_max_body_size 50M` prevents HTTP 413 errors when uploading large high-resolution carrier photos.
3. **Environment Variables**:
   - `STEGSTR_DATA_DIR`: Custom data storage directory.
   - `API_HOST`: Set to `0.0.0.0` for Docker, `127.0.0.1` behind Nginx.
   - `API_PORT`: Default `8765`.

---

## 5. Verification Commands

After deployment, run the following verification checklist:

```bash
# 1. API Status Check
curl -s https://stegstr.yourdomain.com/api/v1/status | jq .

# 2. Relays Health Check
curl -s https://stegstr.yourdomain.com/api/v1/relays | jq .

# 3. CLI Remote Connectivity Test
./stegstr-cli test --json
```
