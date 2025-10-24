# Complete Server Setup Guide

## Overview

This guide covers setting up a fresh GPU server for Finance Agent deployment, including:
- Docker & Docker Compose
- Security patches & automatic updates
- Nginx web server
- SSL certificates
- Firewall & SSH protection
- GPU support (nvidia-docker)

## Server Specifications

### Your 8GB VRAM Server

| Component | Specification |
|-----------|--------------|
| **GPU** | 8GB VRAM, CUDA 13.0, 4.9 TFLOPS |
| **CPU** | Intel Xeon W-2133 (6/12 cores) |
| **RAM** | 64.2 GB |
| **Storage** | 130 GB NVMe (4083 MB/s) |
| **Network** | 2035 Mbps down / 1492 Mbps up |
| **PCIe** | 3.0/16x (11.7 GB/s) |

**Recommended Model**: `llama3.1:8b-instruct` (Q4 quantization, uses ~6GB VRAM)

---

## 🚀 Quick Setup (Automated)

### Step 1: Provision Server

```bash
# SSH into your new server
ssh user@your-server-ip

# Download provisioning script
wget https://raw.githubusercontent.com/yourusername/financeagent/main/scripts/provision_server.sh

# Make executable and run
chmod +x provision_server.sh
./provision_server.sh
```

**What it does:**
1. ✅ Updates system with latest security patches
2. ✅ Enables automatic security updates
3. ✅ Installs Docker & Docker Compose
4. ✅ Installs nvidia-docker2 for GPU support
5. ✅ Installs Nginx web server
6. ✅ Installs Certbot for SSL certificates
7. ✅ Configures UFW firewall
8. ✅ Sets up Fail2Ban for SSH protection
9. ✅ Applies system optimizations
10. ✅ Creates Nginx configuration template

**Time**: ~10-15 minutes

### Step 2: Log Out and Back In

```bash
# Log out (for docker group changes)
exit

# Log back in
ssh user@your-server-ip
```

### Step 3: Deploy Finance Agent

```bash
# Clone repository
git clone https://github.com/yourusername/financeagent.git
cd financeagent

# Run deployment script
./scripts/gpu_deploy.sh
```

The deployment script will:
- Auto-detect your 8GB GPU
- Select optimal model for your VRAM
- Configure all services
- Download AI models
- Initialize databases

**Time**: ~15-20 minutes (mostly downloading models)

### Step 4: Configure Nginx & Domain

```bash
# Copy template
sudo cp /etc/nginx/sites-available/financeagent.template /etc/nginx/sites-available/financeagent

# Edit configuration (replace 'yourdomain.com' with your actual domain)
sudo nano /etc/nginx/sites-available/financeagent

# Enable site
sudo ln -s /etc/nginx/sites-available/financeagent /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 5: Get SSL Certificate

```bash
# Make sure DNS is pointing to your server first!
# Then run:
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certbot will automatically:
# - Get SSL certificate from Let's Encrypt
# - Configure Nginx for HTTPS
# - Set up auto-renewal
```

### Step 6: Enable Firewall

```bash
# IMPORTANT: Make sure SSH is working before enabling!
sudo ufw enable

# Check status
sudo ufw status
```

---

## 📋 Manual Setup (Step-by-Step)

If you prefer manual control:

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo apt dist-upgrade -y

# Install essentials
sudo apt install -y curl wget git vim htop build-essential
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
exit
ssh user@your-server-ip
```

### 3. Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker-compose --version
```

### 4. Install nvidia-docker2

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

# Add repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt update
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### 5. Install Nginx

```bash
sudo apt install -y nginx

# Stop for now (will configure later)
sudo systemctl stop nginx
```

### 6. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 7. Configure Firewall

```bash
sudo apt install -y ufw

# Configure rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Enable (AFTER verifying SSH works!)
sudo ufw enable
```

### 8. Install Fail2Ban

```bash
sudo apt install -y fail2ban

# Configure
sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 🔒 Security Hardening

### Automatic Security Updates

```bash
sudo apt install -y unattended-upgrades

# Configure
sudo dpkg-reconfigure -plow unattended-upgrades
```

### SSH Hardening

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Recommended changes:
# PermitRootLogin no
# PasswordAuthentication no  # After setting up SSH keys!
# Port 2222  # Change default port (optional)

# Restart SSH
sudo systemctl restart sshd
```

### SSH Key Authentication

```bash
# On your local machine:
ssh-keygen -t ed25519 -C "your-email@example.com"
ssh-copy-id user@your-server-ip

# Test
ssh user@your-server-ip

# Then disable password auth (see SSH hardening above)
```

---

## 🌐 Nginx Configuration

### Basic Configuration

Create `/etc/nginx/sites-available/financeagent`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    # API Docs
    location /docs {
        proxy_pass http://localhost:8000;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/financeagent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
# Make sure DNS is configured first!
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## 📊 Performance Tuning

### For 8GB VRAM GPU

```bash
# In your .env file:
OLLAMA_MODEL=llama3.1:8b-instruct  # Q4, uses ~6GB VRAM
EMBEDDING_MODEL=nomic-embed-text
CHUNK_SIZE=1024
TOP_K=5
```

### System Optimizations

```bash
# Add to /etc/sysctl.conf
sudo tee -a /etc/sysctl.conf << EOF
fs.file-max = 65536
fs.inotify.max_user_watches = 524288
net.core.somaxconn = 1024
EOF

sudo sysctl -p
```

---

## 🔍 Monitoring & Maintenance

### Check Services

```bash
# Docker containers
docker-compose -f docker-compose.prod.yml ps

# Nginx
sudo systemctl status nginx

# Firewall
sudo ufw status

# Fail2Ban
sudo fail2ban-client status sshd

# GPU
nvidia-smi
watch -n 1 nvidia-smi
```

### View Logs

```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -f

# Auth logs (SSH attempts)
sudo tail -f /var/log/auth.log

# Fail2Ban logs
sudo tail -f /var/log/fail2ban.log
```

### Backups

```bash
# Backup PostgreSQL
docker exec financeagent_postgres pg_dump -U postgres financeagent > backup_$(date +%Y%m%d).sql

# Backup Qdrant
docker exec financeagent_qdrant tar czf - /qdrant/storage > qdrant_backup_$(date +%Y%m%d).tar.gz

# Backup .env
cp .env .env.backup
```

---

## 🐛 Troubleshooting

### Docker GPU Not Working

```bash
# Check GPU
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Restart Docker
sudo systemctl restart docker
```

### Nginx Not Starting

```bash
# Check configuration
sudo nginx -t

# Check logs
sudo journalctl -u nginx -f

# Check port conflicts
sudo lsof -i :80
sudo lsof -i :443
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew

# Check renewal timer
sudo systemctl status certbot.timer
```

### Firewall Blocking Access

```bash
# Check rules
sudo ufw status verbose

# Allow specific port
sudo ufw allow 8000/tcp

# Disable temporarily (for testing)
sudo ufw disable
```

---

## 📚 Additional Resources

- [SERVER_SPECS.md](SERVER_SPECS.md) - Server specifications
- [DEPLOYMENT.md](DEPLOYMENT.md) - General deployment guide
- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) - CI/CD automation

---

## ✅ Post-Setup Checklist

- [ ] System updated with latest security patches
- [ ] Automatic security updates enabled
- [ ] Docker and Docker Compose installed
- [ ] nvidia-docker2 installed and GPU accessible
- [ ] Nginx installed and configured
- [ ] SSL certificate obtained and configured
- [ ] Firewall enabled and configured
- [ ] Fail2Ban protecting SSH
- [ ] SSH key authentication set up
- [ ] Finance Agent deployed and running
- [ ] Domain DNS configured
- [ ] Monitoring set up
- [ ] Backup strategy in place

---

**Your server is now production-ready!** 🚀
