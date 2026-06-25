# StudyNova Deployment Guide

This guide provides step-by-step instructions for deploying StudyNova to production.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Cloudinary Setup](#cloudinary-setup)
5. [Email Configuration](#email-configuration)
6. [Deployment Options](#deployment-options)
7. [Post-Deployment](#post-deployment)
8. [Maintenance](#maintenance)

## Prerequisites

- Python 3.8 or higher
- MySQL 8.0+ or SQLite3
- Git
- Domain name (optional but recommended)
- SSL certificate (for production)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Sharanabasu123/StudyNova.git
cd StudyNova
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
STUDYNOVA_SECRET_KEY=your-secret-key-here-generate-a-random-string
STUDYNOVA_ADMIN_EMAIL=admin@studynova.com
STUDYNOVA_ADMIN_PASSWORD=your-secure-admin-password
STUDYNOVA_ADMIN_NAME=StudyNova Admin
STUDYNOVA_CREATE_DEMO_USER=1

# Database Configuration (MySQL - Recommended for Production)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=studynova
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=studynova

# Email Configuration (Gmail SMTP)
MAIL_USERNAME=studynovaofficial@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587

# Cloudinary Configuration (Optional - for file storage)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Application URL
APP_URL=https://studynova.com
```

## Database Configuration

### Option A: MySQL (Recommended for Production)

#### 1. Install MySQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# Windows
# Download from https://dev.mysql.com/downloads/mysql/
```

#### 2. Create Database and User

```sql
CREATE DATABASE studynova CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'studynova'@'localhost' IDENTIFIED BY 'your-secure-password';
GRANT ALL PRIVILEGES ON studynova.* TO 'studynova'@'localhost';
FLUSH PRIVILEGES;
```

#### 3. Update Environment Variables

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=studynova
MYSQL_PASSWORD=your-secure-password
MYSQL_DATABASE=studynova
```

### Option B: SQLite (Development Only)

No configuration needed. The application will automatically create `studynova.db` on first run.

**Note:** SQLite is not recommended for production due to concurrency limitations.

## Cloudinary Setup

Cloudinary is used for file storage and CDN delivery.

### 1. Create Cloudinary Account

1. Sign up at [cloudinary.com](https://cloudinary.com/)
2. Get your credentials from the Dashboard

### 2. Configure Environment Variables

```env
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 3. Without Cloudinary

If you don't configure Cloudinary, files will be stored locally in the `uploads/` directory. This is suitable for development but not recommended for production.

## Email Configuration

### Gmail SMTP Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. Use the generated password in `MAIL_PASSWORD`

### Alternative Email Providers

```env
# For Outlook/Office365
MAIL_SMTP_HOST=smtp.office365.com
MAIL_SMTP_PORT=587

# For SendGrid
MAIL_SMTP_HOST=smtp.sendgrid.net
MAIL_SMTP_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

## Deployment Options

### Option 1: Gunicorn + Nginx (Recommended)

#### 1. Install Gunicorn

```bash
pip install gunicorn
```

#### 2. Test Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/studynova.service`:

```ini
[Unit]
Description=StudyNova Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/StudyNova
Environment="PATH=/path/to/StudyNova/venv/bin"
EnvironmentFile=/path/to/StudyNova/.env
ExecStart=/path/to/StudyNova/venv/bin/gunicorn --workers 3 --bind unix:studynova.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

#### 4. Start the Service

```bash
sudo systemctl start studynova
sudo systemctl enable studynova
sudo systemctl status studynova
```

#### 5. Configure Nginx

Create `/etc/nginx/sites-available/studynova`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";
    
    # Static files
    location /static/ {
        alias /path/to/StudyNova/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads/ {
        alias /path/to/StudyNova/uploads/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Main application
    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/StudyNova/studynova.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Client upload size
    client_max_body_size 16M;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/studynova /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. Setup SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root-password
      MYSQL_DATABASE: studynova
      MYSQL_USER: studynova
      MYSQL_PASSWORD: studynova-password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    restart: always

  studynova:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_USER=studynova
      - MYSQL_PASSWORD=studynova-password
      - MYSQL_DATABASE=studynova
      - STUDYNOVA_SECRET_KEY=your-secret-key
      - MAIL_USERNAME=your-email@gmail.com
      - MAIL_PASSWORD=your-app-password
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - mysql
    restart: always

volumes:
  mysql_data:
```

#### 3. Deploy with Docker Compose

```bash
docker-compose up -d
docker-compose logs -f
```

### Option 3: Heroku Deployment

#### 1. Install Heroku CLI

```bash
# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli

# Linux/Mac
curl https://cli-assets.heroku.com/install.sh | sh
```

#### 2. Create Procfile

```
web: gunicorn app:app
```

#### 3. Deploy

```bash
heroku login
heroku create studynova-app
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku config:set STUDYNOVA_SECRET_KEY=your-secret-key
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-app-password
```

### Option 4: PythonAnywhere

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com/)
2. Upload your code via Git or file upload
3. Create a virtual environment
4. Install dependencies
5. Configure the web app in the Web tab
6. Set up environment variables

## Post-Deployment

### 1. Initialize Database

The database will be automatically initialized on first run. Verify:

```bash
# Check logs
sudo journalctl -u studynova -f

# Or check application logs
tail -f /path/to/StudyNova/logs/app.log
```

### 2. Create Admin User

If no admin user was created automatically:

```python
python -c "
from app import create_admin_user
create_admin_user('admin@studynova.com', 'secure-password', 'Admin Name')
"
```

### 3. Test the Application

1. Visit your domain
2. Test user registration
3. Test login
4. Test file upload
5. Test admin panel
6. Test email notifications

### 4. Setup Monitoring

#### Application Monitoring

```bash
# Install monitoring tools
pip install sentry-sdk[flask]
```

Add to `app.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()]
)
```

#### Log Management

```bash
# Install log rotation
sudo nano /etc/logrotate.d/studynova

/path/to/StudyNova/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}
```

## Maintenance

### Regular Tasks

1. **Database Backups**
   ```bash
   # MySQL
   mysqldump -u studynova -p studynova > backup_$(date +%Y%m%d).sql
   
   # SQLite
   cp studynova.db backup_$(date +%Y%m%d).db
   ```

2. **Update Dependencies**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

3. **Monitor Disk Space**
   ```bash
   df -h
   du -sh uploads/*
   ```

4. **Review Logs**
   ```bash
   tail -f /var/log/nginx/error.log
   sudo journalctl -u studynova -f
   ```

### Scaling

#### Horizontal Scaling

1. Increase Gunicorn workers:
   ```bash
   gunicorn --workers 4 --bind unix:studynova.sock app:app
   ```

2. Use a load balancer (nginx, HAProxy)

3. Deploy multiple application servers

#### Database Scaling

1. Enable MySQL query cache
2. Add database indexes
3. Consider read replicas for high traffic

### Security Checklist

- [ ] Enable HTTPS with SSL certificate
- [ ] Set strong SECRET_KEY
- [ ] Use environment variables for secrets
- [ ] Enable firewall (ufw/iptables)
- [ ] Regular security updates
- [ ] Limit file upload size
- [ ] Validate all user inputs
- [ ] Use parameterized queries (already implemented)
- [ ] Enable CORS only if needed
- [ ] Regular backups
- [ ] Monitor for suspicious activity

### Troubleshooting

#### Application Won't Start

```bash
# Check logs
sudo journalctl -u studynova -n 50

# Check permissions
ls -la /path/to/StudyNova/
sudo chown -R www-data:www-data /path/to/StudyNova/
```

#### Database Connection Issues

```bash
# Test MySQL connection
mysql -u studynova -p -h localhost

# Check MySQL service
sudo systemctl status mysql
```

#### File Upload Issues

```bash
# Check uploads directory permissions
ls -la uploads/
sudo chmod 755 uploads/
sudo chown www-data:www-data uploads/
```

#### Email Not Sending

```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('SMTP connection successful')
server.quit()
"
```

## Performance Optimization

1. **Enable Gzip Compression** (in nginx)
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
   ```

2. **Use CDN** for static files (Cloudinary already provides this)

3. **Database Indexing**
   ```sql
   CREATE INDEX idx_resources_subject ON resources(subject_id);
   CREATE INDEX idx_resources_approved ON resources(is_approved);
   CREATE INDEX idx_users_email ON users(email);
   ```

4. **Cache Frequently Accessed Data**
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   
   @cache.cached(timeout=50)
   def get_schemes():
       # ...
   ```

## Support

For issues and questions:
- GitHub Issues: https://github.com/Sharanabasu123/StudyNova/issues
- Email: studynovaofficial@gmail.com

## License

This project is licensed under the MIT License.