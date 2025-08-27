# Cloud VPS Setup Guide for 24/7 Property Scraping

## 🌐 ALWAYS-ON CLOUD SCRAPER SETUP

### **Recommended Cloud Providers:**
1. **DigitalOcean Droplet** - $4/month
2. **AWS EC2 t3.nano** - ~$3-5/month  
3. **Google Cloud Compute** - $3-7/month
4. **Linode** - $5/month

### **Setup Steps:**

#### 1. Create Cloud Server
- Ubuntu 22.04 LTS
- 1GB RAM, 1 CPU (minimum)
- SSH access enabled

#### 2. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Install PostgreSQL client
sudo apt install postgresql-client -y
```

#### 3. Deploy Scraper
```bash
# Clone your repository
git clone https://github.com/yourusername/property-finder.git
cd property-finder/scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
nano .env  # Add your DATABASE_URL
```

#### 4. Setup Cron Job
```bash
# Edit crontab
crontab -e

# Add this line for daily 2 AM run:
0 2 * * * cd /home/ubuntu/property-finder/scraper && /home/ubuntu/property-finder/scraper/venv/bin/python daily_scraper.py >> /var/log/scraper.log 2>&1
```

#### 5. Test Setup
```bash
# Test scraper manually
cd /home/ubuntu/property-finder/scraper
source venv/bin/activate
python daily_scraper.py

# Check logs
tail -f /var/log/scraper.log
```

### **Monthly Cost:** $3-7/month
### **Uptime:** 99.9% (runs even when your PC is off)

### **Pros:**
- ✅ True 24/7 operation
- ✅ Independent of your PC
- ✅ Full control over environment
- ✅ Can handle more complex scraping

### **Cons:**
- ❌ Monthly cost
- ❌ Requires basic server management
- ❌ Need to maintain security updates
