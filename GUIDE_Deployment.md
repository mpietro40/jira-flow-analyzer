# Jira Analytics Suite - Deployment Guide

## Deployment Options

### 1. Docker Deployment (Recommended)

#### Quick Deploy (30 seconds)

**Windows**:
```bash
deploy.bat
```

**Linux/Mac**:
```bash
chmod +x deploy.sh && ./deploy.sh
```

#### Manual Docker Deployment
```bash
docker-compose up --build -d
```

#### Access Application
- **URL**: http://localhost:5000
- **Unified Dashboard**: All analytics tools in one interface

#### Docker Optimizations
- **Base Image**: Alpine Linux (smallest distro)
- **Multi-stage Build**: Minimal final image size
- **Non-root User**: Enhanced security
- **Health Checks**: Automatic monitoring
- **Persistent Volumes**: Data preservation
- **Memory Limits**: 512MB max, 256MB reserved

#### Persistent Data
- Analysis cache: `/app/analysis_cache`
- PI results: `/app/pi_results`
- Safety data: `/app/safety_data`
- Generated docs: `/app/doc`

#### Docker Troubleshooting
```bash
# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Clean rebuild
docker-compose down
docker system prune -f
docker-compose up --build -d
```

#### Health Check
- Endpoint: http://localhost:5000/health
- Automatic monitoring every 30 seconds

---

### 2. Render.com Deployment

#### Prerequisites
- GitHub account with repository pushed
- Render.com account (free tier available)
- Jira credentials and API tokens

#### Required Files
✅ **Procfile** - Tells Render how to start
```
web: python main_app.py
```

✅ **runtime.txt** - Specifies Python version
```
python-3.11.0
```

✅ **requirements.txt** - Lists all dependencies

#### Step-by-Step Deployment

**1. Prepare Repository**
```bash
git add Procfile runtime.txt requirements.txt main_app.py
git commit -m "Add Render.com deployment files"
git push origin main
```

**2. Deploy on Render.com**
- Sign up/Login to https://render.com
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Select your repository

**3. Configure Service Settings**
- **Name**: `jira-analytics-suite`
- **Region**: Choose closest to users
- **Branch**: `main`
- **Root Directory**: `PerseusLeadTime` (important!)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main_app.py`

**4. Configure Environment Variables**

Required:
- `SECRET_KEY`: Secure random string for Flask sessions
- `FLASK_ENV`: `production`

Optional Jira Configuration:
- `JIRA_BASE_URL`: Your Jira instance URL
- `JIRA_USERNAME`: Your Jira email
- `JIRA_API_TOKEN`: Your Jira API token

**5. Deploy and Test**
- Click "Create Web Service"
- Wait 2-5 minutes for build
- Access at: `https://your-service-name.onrender.com`
- Test health endpoint: `/health`

#### Render.com Troubleshooting

**Build Fails**:
- Check `requirements.txt` in `PerseusLeadTime` directory
- Verify all dependencies correctly listed

**App Won't Start**:
- Check logs in Render dashboard
- Ensure `Procfile` correctly formatted
- Verify `main_app.py` exists

**404 Errors**:
- Check template files included in repository
- Verify `templates/` directory exists

**Jira Connection Issues**:
- Verify environment variables set correctly
- Test Jira credentials locally first
- Check Jira API token permissions

#### Render.com Checklist

**Pre-Deployment**:
- [ ] `Procfile` created
- [ ] `runtime.txt` created
- [ ] `requirements.txt` updated
- [ ] `main_app.py` uses PORT environment variable
- [ ] `main_app.py` has `debug=False`
- [ ] All files committed to Git
- [ ] Repository pushed to GitHub

**Service Configuration**:
- [ ] Name set
- [ ] Region selected
- [ ] Branch: `main`
- [ ] Root Directory: `PerseusLeadTime`
- [ ] Runtime: `Python 3`
- [ ] Build Command set
- [ ] Start Command set

**Environment Variables**:
- [ ] `SECRET_KEY` set
- [ ] `FLASK_ENV` set to `production`
- [ ] Optional Jira variables set

**Testing**:
- [ ] Deployment completed
- [ ] App URL accessible
- [ ] Health check works
- [ ] Dashboard loads
- [ ] All tools accessible

#### Scaling and Performance
- **Free Tier**: Good for testing and small teams
- **Paid Tiers**: Better performance and uptime for production
- **Sleep Mode**: Free tier apps sleep after 15 minutes of inactivity

---

### 3. Test Machine Installation

#### Prerequisites
- Docker and Docker Compose installed
- Git (optional, for cloning)

#### Method 1: Git Clone (Recommended)
```bash
git clone <your-repo-url>
cd PerseusLeadTime
./deploy.sh
```

#### Method 2: File Transfer
Copy these files to test machine:
- `Dockerfile`
- `docker-compose.yml` 
- `requirements-docker.txt`
- `deploy.sh` (Linux/Mac) or `deploy.bat` (Windows)
- All `.py` files
- `templates/` folder
- `static/` folder

#### Deploy on Test Machine

**Linux/Mac**:
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows**:
```bash
deploy.bat
```

#### Access Application
- URL: http://localhost:5000
- Or: http://[test-machine-ip]:5000

#### Quick Commands
```bash
# Start
docker-compose up -d

# Stop  
docker-compose down

# Logs
docker-compose logs -f

# Status
docker-compose ps
```

---

## Security Considerations

- **Never commit API tokens** to repository
- Use strong `SECRET_KEY` values
- Set `FLASK_ENV=production` for production
- Consider using secret management for sensitive data
- Enable HTTPS in production (use reverse proxy)

## Available Applications

Once deployed, access these tools:
- 📊 **Lead Time Analyzer** - Flow metrics and cycle time analysis
- 📈 **PI Analyzer** - Product Increment analysis  
- 🏃 **Sprint Analyzer** - Sprint forecasting and capacity analysis
- 📋 **Epic Analyzer** - Epic estimate management
- 🏷️ **Epic Fix Version** - Fix version distribution analysis
- 🔍 **Duplicate Detector** - Identify potential duplicate stories
- 📋 **Report Generator** - Custom Jira reports
- 🎯 **Presentation Generator** - PDF presentations
- 🎭 **Psychological Safety** - Team health metrics

---

**🎉 Your Jira Analytics Suite is now deployed and ready to use!**
