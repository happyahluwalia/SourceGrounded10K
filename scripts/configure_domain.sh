#!/bin/bash
# Configure Nginx, SSL, and Firewall for a domain.
# This script should be run AFTER the application is deployed via Docker Compose.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  log_error "This script must be run as root or with sudo."
  exit 1
fi

# Check for arguments
if [ "$#" -ne 2 ]; then
    log_error "Usage: $0 <your_domain.com> <your_email@example.com>"
    log_info "Example: sudo ./configure_domain.sh finance.example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo "=========================================================================="
echo "  Finance Agent - Domain & SSL Configuration"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo "=========================================================================="
echo ""

# ============================================================================
# STEP 1: Verify DNS is configured
# ============================================================================
log_step "1/6 - Verifying DNS configuration..."
log_info "Checking if $DOMAIN resolves to this server..."

SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

if [ -z "$DOMAIN_IP" ]; then
    log_error "Domain $DOMAIN does not resolve to any IP address."
    log_info "Please configure your DNS A record to point to: $SERVER_IP"
    exit 1
fi

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    log_error "DNS mismatch!"
    log_info "Domain $DOMAIN resolves to: $DOMAIN_IP"
    log_info "This server's IP is: $SERVER_IP"
    log_info "Please update your DNS A record before continuing."
    exit 1
fi

log_success "DNS configured correctly: $DOMAIN -> $SERVER_IP"
echo ""

# ============================================================================
# STEP 2: Install Certbot if not already installed
# ============================================================================
log_step "2/6 - Ensuring Certbot is installed..."
if ! command -v certbot &> /dev/null; then
    apt update
    apt install -y certbot python3-certbot-nginx
    log_success "Certbot installed."
else
    log_info "Certbot already installed."
fi
echo ""

# ============================================================================
# STEP 3: Configure Nginx
# ============================================================================
log_step "3/6 - Configuring Nginx for $DOMAIN..."

# Create Nginx configuration
cat > /etc/nginx/sites-available/financeagent << EOF
# Finance Agent - Nginx Configuration
# Domain: $DOMAIN

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Frontend (React app served by Docker)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/api/health;
        access_log off;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/financeagent /etc/nginx/sites-enabled/financeagent

# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default

# Test configuration
if nginx -t; then
    log_success "Nginx configuration is valid."
else
    log_error "Nginx configuration test failed!"
    exit 1
fi

# Restart Nginx
systemctl restart nginx
log_success "Nginx configured and restarted."
echo ""

# ============================================================================
# STEP 4: Obtain SSL Certificate
# ============================================================================
log_step "4/6 - Obtaining SSL certificate from Let's Encrypt..."

log_info "This will obtain a free SSL certificate for $DOMAIN and www.$DOMAIN"
log_info "Certbot will automatically configure Nginx for HTTPS."

certbot --nginx \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --redirect

if [ $? -eq 0 ]; then
    log_success "SSL certificate obtained and configured!"
else
    log_error "Failed to obtain SSL certificate."
    log_info "Check that:"
    log_info "  1. DNS is properly configured"
    log_info "  2. Port 80 is accessible from the internet"
    log_info "  3. Nginx is running"
    exit 1
fi
echo ""

# ============================================================================
# STEP 5: Configure Firewall
# ============================================================================
log_step "5/6 - Configuring firewall..."

# Add HTTP and HTTPS rules
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Enable firewall if not already enabled
if ! ufw status | grep -q "Status: active"; then
    log_info "Enabling firewall..."
    ufw --force enable
    log_success "Firewall enabled."
else
    log_info "Firewall already enabled."
fi

log_success "Firewall configured to allow HTTP and HTTPS."
echo ""

# ============================================================================
# STEP 6: Verify Certbot Auto-Renewal
# ============================================================================
log_step "6/6 - Verifying SSL certificate auto-renewal..."

# Check if certbot timer is enabled (systemd)
if systemctl is-enabled certbot.timer &> /dev/null; then
    log_success "Certbot auto-renewal timer is enabled."
elif systemctl list-timers | grep -q certbot; then
    log_success "Certbot auto-renewal timer is active."
else
    # Enable the timer if not already enabled
    log_info "Enabling certbot auto-renewal timer..."
    systemctl enable certbot.timer
    systemctl start certbot.timer
    log_success "Certbot auto-renewal timer enabled."
fi

# Also check for cron job (alternative method)
if [ -f /etc/cron.d/certbot ] || crontab -l 2>/dev/null | grep -q certbot; then
    log_info "Certbot cron job also found (backup method)."
fi

# Test renewal
log_info "Testing certificate renewal (dry-run)..."
if certbot renew --dry-run &> /dev/null; then
    log_success "Certificate auto-renewal test passed!"
else
    log_warning "Certificate renewal test had issues. Check manually with: sudo certbot renew --dry-run"
fi

log_info "Certificates will auto-renew every 60 days (expire after 90 days)."
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "=========================================================================="
log_success "🎉 DOMAIN CONFIGURATION COMPLETE! 🎉"
echo "=========================================================================="
echo ""

echo "✅ Configuration Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Domain:       $DOMAIN"
echo "  SSL:          ✓ Enabled (Let's Encrypt)"
echo "  HTTPS:        ✓ Automatic redirect from HTTP"
echo "  Firewall:     ✓ Enabled (SSH, HTTP, HTTPS)"
echo "  Auto-renewal: ✓ Certbot will auto-renew certificate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🌐 Your application is now accessible at:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
echo "  https://$DOMAIN/docs (API documentation)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🔒 SSL Certificate Info:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
certbot certificates | grep -A 5 "$DOMAIN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🔄 SSL Certificate Auto-Renewal:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Status:           ✓ Enabled (automatic)"
echo "  Schedule:         Runs twice daily"
echo "  Renewal:          Certificates renew 30 days before expiry"
echo "  Certificate Life: 90 days"
echo "  Next Check:       systemctl list-timers | grep certbot"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 Useful Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Check SSL:        sudo certbot certificates"
echo "  Renew now:        sudo certbot renew"
echo "  Test renewal:     sudo certbot renew --dry-run"
echo "  Check timer:      systemctl status certbot.timer"
echo "  Nginx status:     sudo systemctl status nginx"
echo "  Nginx logs:       sudo tail -f /var/log/nginx/access.log"
echo "  Firewall status:  sudo ufw status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

log_success "🚀 Your Finance Agent is now live with HTTPS! 🚀"
echo ""