# GitHub Actions Setup for RTX 3060 Deployment

## Overview

The GitHub Actions workflow automatically deploys your Finance Agent to the RTX 3060 GPU server when you push to the `main` branch.

## Workflow Steps

1. **Build Docker Images** - Builds backend and frontend images
2. **Push to GHCR** - Pushes images to GitHub Container Registry
3. **Deploy to Server** - SSHs into your RTX 3060 server and updates services

## Required GitHub Secrets

You need to configure these secrets in your GitHub repository:

### Navigate to Settings
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each of the following:

### Required Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GPU_SERVER_HOST` | IP address or hostname of your RTX 3060 server | `192.168.1.100` or `gpu.yourdomain.com` |
| `GPU_SERVER_USER` | SSH username | `root` or `ubuntu` |
| `GPU_SERVER_SSH_KEY` | Private SSH key for authentication | Contents of `~/.ssh/id_rsa` |
| `GPU_SERVER_PORT` | SSH port (optional, defaults to 22) | `22` or `2222` |
| `GPU_SERVER_PATH` | Path to financeagent directory on server (optional) | `/opt/financeagent` |

## Setting Up SSH Key Authentication

### 1. Generate SSH Key (if you don't have one)

On your local machine:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/gpu_server_deploy
```

### 2. Copy Public Key to Server

```bash
ssh-copy-id -i ~/.ssh/gpu_server_deploy.pub user@your-server-ip
```

Or manually:

```bash
# On your server
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add the public key
echo "your-public-key-content" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 3. Add Private Key to GitHub Secrets

```bash
# Copy the private key
cat ~/.ssh/gpu_server_deploy

# Copy the output and paste it into GitHub secret: GPU_SERVER_SSH_KEY
```

### 4. Test SSH Connection

```bash
ssh -i ~/.ssh/gpu_server_deploy user@your-server-ip
```

## Server Preparation

Your RTX 3060 server needs to be set up before automated deployment works:

### One-Time Setup

```bash
# SSH into your server
ssh user@your-server-ip

# Clone the repository
cd /opt  # or your preferred location
git clone https://github.com/yourusername/financeagent.git
cd financeagent

# Run initial deployment
./scripts/gpu_deploy.sh
```

This initial deployment:
- Sets up `.env` file
- Pulls Docker images
- Downloads AI models
- Initializes databases
- Starts all services

### Verify Setup

```bash
# Check services are running
docker-compose -f docker-compose.prod.yml ps

# Check GPU
nvidia-smi

# Test API
curl http://localhost:8000/api/health
```

## How Automated Deployment Works

### Trigger

Deployment is triggered automatically when you push to `main`:

```bash
git add .
git commit -m "Update application"
git push origin main
```

### What Happens

1. **GitHub Actions starts** (takes ~5-10 minutes)
2. **Builds images** - Backend and frontend Docker images
3. **Pushes to GHCR** - Images stored in GitHub Container Registry
4. **SSHs to server** - Connects to your RTX 3060 server
5. **Updates code** - Pulls latest from git
6. **Updates images** - Pulls latest Docker images
7. **Restarts services** - Zero-downtime restart with docker-compose
8. **Verifies** - Shows container status

### Monitoring Deployment

Watch the deployment in GitHub:
1. Go to your repository
2. Click **Actions** tab
3. Click on the latest workflow run
4. Watch the `deploy-gpu-server` job

### Logs

View deployment logs:

```bash
# SSH into server
ssh user@your-server-ip

# View logs
cd /opt/financeagent
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Manual Deployment

If you need to deploy manually (bypass GitHub Actions):

```bash
# SSH into server
ssh user@your-server-ip
cd /opt/financeagent

# Pull latest code
git pull origin main

# Pull latest images (if using GHCR)
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Rollback

If deployment fails, rollback to previous version:

```bash
# SSH into server
ssh user@your-server-ip
cd /opt/financeagent

# Rollback git
git log --oneline  # Find previous commit hash
git checkout <previous-commit-hash>

# Restart with previous version
docker-compose -f docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Deployment Fails

**Check GitHub Actions logs:**
1. Go to Actions tab
2. Click failed workflow
3. Check error messages

**Common issues:**

1. **SSH connection failed**
   - Verify `GPU_SERVER_HOST` is correct
   - Check SSH key is valid
   - Ensure server is accessible

2. **Permission denied**
   - Verify `GPU_SERVER_USER` has sudo/docker permissions
   - Check SSH key is authorized on server

3. **Docker command not found**
   - Ensure Docker is installed on server
   - Add user to docker group: `sudo usermod -aG docker $USER`

4. **Services not starting**
   - Check logs: `docker-compose logs`
   - Verify `.env` file exists and is configured
   - Check disk space: `df -h`

### Manual Intervention Needed

If automated deployment fails, you can always deploy manually:

```bash
ssh user@your-server-ip
cd /opt/financeagent
./scripts/gpu_deploy.sh  # Re-run deployment script
```

## Security Best Practices

1. **Use dedicated SSH key** - Don't reuse your personal SSH key
2. **Restrict SSH key** - Add to `authorized_keys` with restrictions:
   ```bash
   command="cd /opt/financeagent && git pull && docker-compose up -d",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA...
   ```
3. **Use non-root user** - Create dedicated deployment user
4. **Enable firewall** - Only allow necessary ports
5. **Monitor deployments** - Set up alerts for failed deployments

## Alternative: Manual Deployment Only

If you prefer not to use automated deployment, you can disable it:

1. Edit `.github/workflows/deploy.yml`
2. Change line 65 to: `if: github.ref == 'refs/heads/main' && false`
3. Deploy manually when needed

## Next Steps

After setting up GitHub Actions:

1. ✅ Configure GitHub secrets
2. ✅ Test SSH connection
3. ✅ Run initial server setup
4. ✅ Push to main and verify deployment
5. ✅ Monitor first automated deployment
6. ✅ Set up monitoring/alerts

---

**Questions?** Check the main [SERVER_SPECS.md](SERVER_SPECS.md) or [DEPLOYMENT.md](DEPLOYMENT.md)
