#!/bin/bash
# Server Provisioning Script for Finance Agent
# Run as root. Sets up Docker, security, and creates a non-root deployer user.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

echo "=========================================================================="
echo "  Finance Agent - Server Provisioning"
echo "=========================================================================="

if [ "$EUID" -ne 0 ]; then
  log_error "This script must be run as root."
  exit 1
fi

# ============================================================================
# STEP 1: System Update & Essential Packages
# ============================================================================
log_step "1/8 - Updating system and applying security patches..."
apt update
apt upgrade -y
apt install -y curl wget git vim nano htop ufw fail2ban unattended-upgrades screen
log_success "System updated and essential packages installed."

# ============================================================================
# STEP 2: Configure Automatic Security Updates
# ============================================================================
log_step "2/8 - Configuring automatic security updates..."
cat << 'EOF' > /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Package-Blacklist {
    // Add packages to exclude here
};
EOF
systemctl enable unattended-upgrades && systemctl start unattended-upgrades
log_success "Automatic security updates configured."

# ============================================================================
# STEP 3: Install Docker & Docker Compose
# ============================================================================
log_step "3/8 - Installing Docker and Docker Compose..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  rm get-docker.sh
fi
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
log_success "Docker and Docker Compose installed."

# ============================================================================
# STEP 4: Install NVIDIA Docker Toolkit for GPU Support
# ============================================================================
log_step "4/8 - Installing NVIDIA Docker Toolkit..."
if command -v nvidia-smi &> /dev/null; then
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    apt update
    apt install -y nvidia-docker2
    systemctl restart docker
    log_success "NVIDIA Docker Toolkit installed."
else
    log_warning "nvidia-smi not found. Skipping NVIDIA Docker Toolkit. The app will run in CPU mode."
fi

# ============================================================================
# STEP 5: Install Nginx
# ============================================================================
log_step "5/8 - Installing Nginx..."
apt install -y nginx
systemctl stop nginx
log_success "Nginx installed (but not configured or started)."

# ============================================================================
# STEP 6: Configure Firewall (UFW)
# ============================================================================
log_step "6/8 - Configuring basic firewall rules..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
log_success "Firewall configured to only allow SSH. It is NOT enabled yet."

# ============================================================================
# STEP 7: Configure Fail2Ban
# ============================================================================
log_step "7/8 - Configuring Fail2Ban for SSH protection..."
cat << 'EOF' > /etc/fail2ban/jail.local
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
[sshd]
enabled = true
EOF
systemctl enable fail2ban && systemctl restart fail2ban
log_success "Fail2Ban configured."

# ============================================================================
# STEP 8: Create Non-Root Deployer User & Grant Sudo
# ============================================================================
log_step "8/8 - Creating non-root \'deployer\' user and granting privileges..."
DEPLOY_USER="deployer"
if id "$DEPLOY_USER" &>/dev/null; then
    log_warning "User $DEPLOY_USER already exists. Ensuring permissions are correct."
else
    adduser --disabled-password --gecos "" $DEPLOY_USER
    log_success "User $DEPLOY_USER created."
fi

usermod -aG docker $DEPLOY_USER
usermod -aG sudo $DEPLOY_USER
log_info "User $DEPLOY_USER added to \'docker\' and \'sudo\' groups."

# Configure passwordless sudo for the deployer user
SUDOERS_FILE="/etc/sudoers.d/90-deployer-nopasswd"
echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: ALL" > "$SUDOERS_FILE"
chmod 0440 "$SUDOERS_FILE"
log_success "Configured passwordless sudo for $DEPLOY_USER."

# Copy root's SSH key to the new user for seamless login
if [ -f /root/.ssh/authorized_keys ]; then
    mkdir -p /home/$DEPLOY_USER/.ssh
    cp /root/.ssh/authorized_keys /home/$DEPLOY_USER/.ssh/authorized_keys
    chown -R $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh
    chmod 700 /home/$DEPLOY_USER/.ssh
    chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
    log_success "Copied root\'s SSH key to $DEPLOY_USER for easy access."
else
    log_warning "Root SSH key not found. You will need to set up SSH for \'$DEPLOY_USER\' manually."
fi

echo "=========================================================================="
log_success "🎉 SERVER PROVISIONING COMPLETE! 🎉"
echo "=========================================================================="
echo "NEXT STEP: Log out and SSH back in as the 'deployer' user to deploy the application."
echo "ssh deployer@<your-server-ip>"
echo "=========================================================================="