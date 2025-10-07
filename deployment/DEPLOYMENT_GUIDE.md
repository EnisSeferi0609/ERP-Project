# Production Deployment Guide

## Initial Server Setup

### 1. Prerequisites
- Ubuntu/Debian VPS with root access
- Domain name pointed to your server IP
- Docker and Docker Compose installed

### 2. Clone Repository
```bash
cd ~
git clone <your-repo-url> ERP-Project
cd ERP-Project
```

### 3. Configure Environment Variables

Edit `deployment/docker/.env.production` with your actual values:

```bash
nano deployment/docker/.env.production
```

**Required changes:**
- `SECRET_KEY`: Generate with `python -c "import secrets; print('sk_prod_' + secrets.token_hex(50))"`
- `ALLOWED_HOSTS`: Your domain, www subdomain, server IP, and localhost
  - Example: `erp-buildflow.de,www.erp-buildflow.de,123.456.789.012,localhost`

### 4. Configure Nginx

Edit `deployment/nginx/conf.d/app.conf` and replace all instances of `yourdomain.com` with your actual domain:

```bash
nano deployment/nginx/conf.d/app.conf
```

**Replace in 6 places:**
- Line 4, 5: `server_name yourdomain.com www.yourdomain.com;`
- Line 20: `server_name yourdomain.com www.yourdomain.com;`
- Line 23, 24: SSL certificate paths

### 5. Setup SSL Certificates (Let's Encrypt)

```bash
# Install certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Start nginx temporarily to get certificates
cd deployment/docker
docker-compose up -d nginx

# Get certificates
sudo certbot certonly --webroot -w /var/www/certbot \
  -d yourdomain.com -d www.yourdomain.com

# Stop temporary nginx
docker-compose down
```

### 6. Initialize Database

```bash
# Create required directories
mkdir -p data logs receipts rechnungen certbot

# Create database
python3 scripts/create_db.py
```

### 7. Start Application

```bash
cd deployment/docker
docker-compose up -d --build
```

### 8. Initial Setup

Visit `https://yourdomain.com/setup` to create your admin account.

---

## Git Configuration for Production

After initial setup, tell git to ignore your production-specific config changes:

```bash
cd ~/ERP-Project
git update-index --skip-worktree deployment/docker/.env.production
git update-index --skip-worktree deployment/nginx/conf.d/app.conf
```

This allows you to pull code updates without overwriting your production configs.

---

## Updating Production Code

When you have code changes to deploy:

```bash
cd ~/ERP-Project

# Pull latest code (your configs remain untouched)
git pull origin main

# Rebuild and restart
cd deployment/docker
docker-compose down
docker-compose up -d --build
```

---

## Automatic Certificate Renewal

Add to crontab for automatic renewal:

```bash
sudo crontab -e
```

Add this line:
```
0 3 * * * certbot renew --quiet --deploy-hook "docker-compose -f /root/ERP-Project/deployment/docker/docker-compose.yml restart nginx"
```

---

## Monitoring and Logs

```bash
# View application logs
docker-compose logs -f app

# View nginx logs
docker-compose logs -f nginx

# Check application health
curl https://yourdomain.com/health

# Application logs (inside container)
docker-compose exec app cat /app/logs/buildflow.log
```

---

## Backup Strategy

### Database Backup
```bash
# Create backup
cp data/erp.db data/erp.db.backup-$(date +%Y%m%d)

# Automated daily backup (add to crontab)
0 2 * * * cp /root/ERP-Project/data/erp.db /root/ERP-Project/data/erp.db.backup-$(date +\%Y\%m\%d)
```

### Files Backup
```bash
# Backup receipts and invoices
tar -czf backup-files-$(date +%Y%m%d).tar.gz receipts/ rechnungen/
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose up -d --build --force-recreate
```

### SSL certificate issues
```bash
# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Database locked errors
```bash
# Check if multiple processes are accessing DB
docker-compose ps
docker-compose restart app
```

---
