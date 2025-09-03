# Jira Analytics Suite - Unified Web Application

## Overview
The Jira Analytics Suite provides a unified web interface to access all your Jira analytics tools from a single dashboard. This approach maintains the integrity of each individual application while providing a seamless user experience.

## 🚀 Quick Start

### Option 1: Use the Launcher (Recommended)
```bash
python launcher.py
```
Then select option 1 for the unified suite.

### Option 2: Direct Launch
```bash
python main_app.py
```

The unified suite will be available at: **http://localhost:5000**

## 📊 Available Applications

### 1. Lead Time Analyzer
- **Purpose**: Flow metrics and cycle time analysis
- **Features**: WIP tracking, throughput analysis, cycle time measurement
- **Access**: Dashboard → Lead Time Analyzer

### 2. PI Analyzer  
- **Purpose**: Product Increment completion analysis
- **Features**: Cross-project tracking, automatic discovery, flow metrics
- **Access**: Dashboard → PI Analyzer

### 3. Sprint Analyzer
- **Purpose**: Sprint forecasting and capacity analysis  
- **Features**: Historical velocity, Monte Carlo simulation, risk assessment
- **Access**: Dashboard → Sprint Analyzer

### 4. Epic Analyzer
- **Purpose**: Epic estimate management and synchronization
- **Features**: Epic-child comparison, progress tracking, API updates
- **Access**: Dashboard → Epic Analyzer

### 5. Presentation Generator
- **Purpose**: Generate professional PDF presentations
- **Features**: Automated slide generation, professional formatting
- **Access**: Navigation → Generate Presentation

## 🏗️ Architecture

### Unified vs Individual Apps
- **Unified Suite** (`main_app.py`): Single application with all tools integrated
- **Individual Apps**: Each tool can still run independently
  - `app.py` - Lead Time Analyzer (Port 5100)
  - `pi_web_app.py` - PI Analyzer (Port 5300) 
  - `sprint_web_app.py` - Sprint Analyzer (Port 5200)

### Benefits of Unified Approach
✅ **Single Entry Point**: One URL for all tools  
✅ **Consistent UI**: Unified navigation and styling  
✅ **Shared Resources**: Common components and configurations  
✅ **Easy Deployment**: Single application to deploy  
✅ **Preserved Functionality**: All individual app features maintained  

### Benefits of Individual Apps
✅ **Isolation**: Each app runs independently  
✅ **Specialized**: Focused on specific use cases  
✅ **Scalability**: Can be deployed separately  
✅ **Development**: Easier to maintain individual features  

## 🔧 Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key-here  # Optional, defaults to dev key
```

### Dependencies
All existing dependencies are preserved. The unified app uses the same:
- Flask framework
- Jira API clients
- PDF generators
- Data analyzers
- Visualization components

## 🚦 Running Options

### 1. Unified Suite (Port 5000)
```bash
python main_app.py
# or
python launcher.py → Option 1
```

### 2. Individual Applications
```bash
# Lead Time Analyzer
python app.py  # Port 5100

# PI Analyzer  
python pi_web_app.py  # Port 5300

# Sprint Analyzer
python sprint_web_app.py  # Port 5200
```

### 3. Presentation Only
```bash
python presentation_generator.py
# or
python launcher.py → Option 6
```

## 📁 File Structure
```
PerseusLeadTime/
├── main_app.py              # 🌟 Unified suite application
├── launcher.py              # 🚀 Application launcher
├── templates/
│   └── dashboard.html       # 📊 Main dashboard template
├── app.py                   # Individual: Lead Time Analyzer
├── pi_web_app.py           # Individual: PI Analyzer
├── sprint_web_app.py       # Individual: Sprint Analyzer
└── [existing files...]     # All existing functionality preserved
```

## 🔒 Security & Performance
- All existing security measures preserved
- Rate limiting maintained
- Input validation unchanged
- API safety features intact
- Performance optimizations retained

## 🎯 Use Cases

### For Management/Stakeholders
- Use **Unified Suite** for comprehensive overview
- Generate presentations for executive reporting
- Access all metrics from single interface

### For Development Teams
- Use **Individual Apps** for focused analysis
- Deep dive into specific metrics
- Specialized workflows for each tool

### For Agile Coaches
- Use **Unified Suite** for coaching sessions
- Switch between tools seamlessly
- Generate comprehensive reports

## 🆘 Troubleshooting

### Port Conflicts
If port 5000 is in use:
```python
# Edit main_app.py, change the last line:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
```

### Individual App Issues
Each individual app maintains its original functionality:
- Check individual README files for specific troubleshooting
- All existing error handling preserved
- Log files remain in same locations

### Dependencies
```bash
pip install -r requirements.txt  # Same requirements as before
```

## 🔄 Migration Guide

### From Individual Apps
1. **No changes needed** - individual apps still work
2. **Optional**: Use unified suite for better UX
3. **Gradual adoption**: Start with unified, fall back to individual if needed

### Preserving Existing Workflows
- All existing URLs and endpoints preserved in individual apps
- All configuration files remain unchanged
- All data formats and exports identical
- All PDF reports maintain same format

## 📈 Future Enhancements
- User authentication and role-based access
- Saved configurations and favorites
- Cross-application data correlation
- Enhanced dashboard with widgets
- API endpoints for external integration

---

**Author**: Pietro Maffi  
**Purpose**: Unified access to Jira analytics tools while preserving individual application integrity