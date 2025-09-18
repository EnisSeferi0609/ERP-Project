# BuildFlow ERP - Deployment Guide

## 🚀 Production Deployment with Docker

### Prerequisites
- VPS with Ubuntu 20.04+ (minimum 1GB RAM, 1 CPU, 25GB storage)
- Domain name pointing to your VPS IP
- Docker and Docker Compose installed

### Step 1: VPS Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Deploy Application
```bash
# Clone your repository
git clone <your-repo-url>
cd ERP-Projekt

# Create necessary directories
mkdir -p data logs receipts rechnungen certbot/conf certbot/www

# Configure environment
cp deployment/docker/.env.production deployment/docker/.env.production.local
```

### Step 3: Configure Production Settings

#### Edit `.env.production`:
```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update deployment/docker/.env.production with:
SECRET_KEY=<generated-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

#### Update nginx configuration:
```bash
# Replace 'yourdomain.com' with your actual domain in:
# - deployment/nginx/conf.d/app.conf
```

### Step 4: Get SSL Certificate
```bash
# Initial certificate (HTTP challenge)
docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot --email your-email@domain.com --agree-tos --no-eff-email -d yourdomain.com -d www.yourdomain.com
```

### Step 5: Start Application
```bash
# Navigate to deployment directory
cd deployment/docker

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### Step 6: First Setup
1. Visit `https://yourdomain.com`
2. Complete the setup wizard to create your admin account
3. Start using your ERP system!

## 🔧 Management Commands

### Application Management
```bash
# View logs
docker-compose logs -f app

# Restart application
docker-compose restart app

# Update application
git pull
docker-compose build app
docker-compose up -d

# Backup database
docker-compose exec app cp /app/data/erp.db /app/data/backup-$(date +%Y%m%d).db
```

### SSL Certificate Renewal
```bash
# Certificates auto-renew, but to force renewal:
docker-compose exec certbot certbot renew
docker-compose restart nginx
```

## 📊 Monitoring

### Health Check
```bash
curl https://yourdomain.com/health
```

### System Resources
```bash
# Check container status
docker-compose ps

# Monitor resource usage
docker stats
```

## 🔒 Security Considerations

### Firewall Setup
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### Regular Maintenance
- Update system packages monthly
- Monitor disk space (database and uploads)
- Review access logs for suspicious activity
- Backup database weekly

## 💰 Cost Breakdown
- **VPS**: $5-10/month (DigitalOcean, Linode, Vultr)
- **Domain**: $10-15/year
- **SSL Certificate**: Free (Let's Encrypt)
- **Total**: ~$5-15/month

## 🆘 Troubleshooting

### Common Issues
1. **App won't start**: Check logs with `docker-compose logs app`
2. **SSL issues**: Verify domain DNS and certificate generation
3. **Database errors**: Check permissions and disk space
4. **502 errors**: Ensure app container is healthy

### Support
- Check application logs in `logs/` directory
- Monitor nginx logs: `docker-compose logs nginx`
- Database location: `data/erp.db`