# Installation Checklist - Jira User Access Auditor

## Pre-Installation Checklist

- [ ] **Python 3.8+ installed**
  - Download from: https://www.python.org/downloads/
  - ⚠️ IMPORTANT: Check "Add Python to PATH" during installation
  - Test: Open Command Prompt and type `python --version`

- [ ] **Jira API Token created**
  - Go to: https://id.atlassian.com/manage-profile/security/api-tokens
  - Click "Create API token"
  - Name it: "User Auditor"
  - Copy and save the token securely

- [ ] **Know your Jira URL**
  - Example: https://yourcompany.atlassian.net
  - Example: https://jira.yourcompany.com

- [ ] **Know the project key to audit**
  - Example: PROJ, DEV, ISDOP
  - Must be uppercase

---

## Installation Steps

### Step 1: Install Required Libraries
- [ ] Open Command Prompt in the application folder
- [ ] Run: `pip install -r user_auditor_requirements.txt`
- [ ] Wait for "Successfully installed" message
- [ ] Expected time: ~30 seconds

**What gets installed:**
- Flask 3.0.0 (Web framework)
- requests 2.31.0 (HTTP library)
- Werkzeug 3.0.1 (Flask dependency)

---

## First Run Checklist

### Step 2: Start the Application
- [ ] Double-click `run_user_auditor.bat`
  OR
- [ ] Run in Command Prompt: `python jira_user_auditor.py`
- [ ] Wait for message: "Running on http://0.0.0.0:5201"
- [ ] Keep the Command Prompt window open

### Step 3: Open Web Interface
- [ ] Open your web browser
- [ ] Go to: http://localhost:5201
- [ ] You should see "Jira User Access Auditor" page

### Step 4: Enter Connection Details
- [ ] **Jira Server URL**: Enter your Jira URL
- [ ] **API Token**: Paste your API token
- [ ] **Project Key**: Enter project to audit (uppercase)
- [ ] **Company Email Domains**: Enter your company domain(s)

### Step 5: Run First Audit
- [ ] Click "Audit Single Project" button
- [ ] Wait for scan to complete (10-60 seconds)
- [ ] Review the results

### Step 6: Verify Results
- [ ] Summary section shows correct numbers
- [ ] External users table displays users
- [ ] Company users table displays users
- [ ] Export to CSV works

---

## Troubleshooting Checklist

### If Python is not found:
- [ ] Reinstall Python with "Add to PATH" checked
- [ ] Restart Command Prompt after installation
- [ ] Try: `py --version` instead of `python --version`

### If libraries fail to install:
- [ ] Check internet connection
- [ ] Try: `python -m pip install -r user_auditor_requirements.txt`
- [ ] Try: `pip install Flask requests`
- [ ] Update pip: `python -m pip install --upgrade pip`

### If connection to Jira fails:
- [ ] Verify Jira URL is correct (copy from browser)
- [ ] Check API token is valid (create new one if needed)
- [ ] Test Jira URL in browser (should be accessible)
- [ ] Check firewall/proxy settings

### If no users found:
- [ ] Verify project key is correct (must be uppercase)
- [ ] Check you have access to the project in Jira
- [ ] Ensure API token has project view permissions
- [ ] Try a different project you know exists

### If port 5201 is in use:
- [ ] Close other applications using port 5201
- [ ] Edit `jira_user_auditor.py`, change port number in last line
- [ ] Try port 5202, 5300, or 8080

---

## Success Indicators

✅ **Installation Successful When:**
- Python version displays correctly
- All libraries install without errors
- No red error messages

✅ **Application Running When:**
- Command Prompt shows "Running on http://0.0.0.0:5201"
- Browser loads the web interface
- No error messages in Command Prompt

✅ **Audit Working When:**
- Connection test succeeds
- Results display within 60 seconds
- User tables populate with data
- CSV export downloads successfully

---

## Post-Installation

### Regular Use:
- [ ] Bookmark: http://localhost:5201
- [ ] Save API token securely (password manager)
- [ ] Document company email domains
- [ ] Schedule regular audits (monthly recommended)

### Security:
- [ ] Never share API token
- [ ] Revoke token when no longer needed
- [ ] Keep audit results confidential
- [ ] Delete old CSV exports

---

## Quick Reference

**Start Application:**
```
Double-click: run_user_auditor.bat
OR
Command: python jira_user_auditor.py
```

**Access Application:**
```
http://localhost:5201
```

**Stop Application:**
```
Press Ctrl+C in Command Prompt window
```

**Reinstall Libraries:**
```
pip install -r user_auditor_requirements.txt --force-reinstall
```

---

## Need Help?

1. Read: USER_AUDITOR_SETUP_GUIDE.md (detailed guide)
2. Read: USER_AUDITOR_README.md (features and usage)
3. Check: Command Prompt for error messages
4. Verify: All checklist items above

---

**Version:** 1.0  
**Last Updated:** January 2025
