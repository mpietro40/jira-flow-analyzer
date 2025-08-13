"""
Generate setup guide PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_setup_guide():
    """Generate comprehensive setup guide PDF."""
    
    doc = SimpleDocTemplate("Jira_Analytics_Setup_Guide.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=10,
        leftIndent=20,
        backgroundColor=colors.lightgrey,
        borderColor=colors.black,
        borderWidth=1,
        borderPadding=5
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Jira Analytics Application", title_style))
    story.append(Paragraph("Complete Setup Guide", styles['Heading2']))
    story.append(Spacer(1, 0.5*inch))
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", styles['Heading2']))
    toc_items = [
        "1. Prerequisites",
        "2. Installation Steps", 
        "3. Configuration",
        "4. Running the Application",
        "5. Using the Dashboard",
        "6. Troubleshooting",
        "7. Development and Testing"
    ]
    
    for item in toc_items:
        story.append(Paragraph(item, styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Prerequisites
    story.append(Paragraph("1. Prerequisites", styles['Heading2']))
    prereq_text = """
    Before setting up the Jira Analytics application, ensure you have:
    
    • Python 3.8 or higher installed
    • pip (Python package installer)
    • Access to a Jira server with API permissions
    • A valid Jira API token
    • Git (for version control)
    • Web browser (Chrome, Firefox, Safari, or Edge)
    """
    story.append(Paragraph(prereq_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Installation Steps
    story.append(Paragraph("2. Installation Steps", styles['Heading2']))
    
    story.append(Paragraph("Step 1: Download the Application", styles['Heading3']))
    story.append(Paragraph("Create a new directory and save all the Python files:", styles['Normal']))
    
    install_code = """
mkdir jira-analytics
cd jira-analytics

# Save all the provided Python files in this directory:
# - app.py
# - jira_client.py  
# - data_analyzer.py
# - visualization.py
# - pdf_generator.py
# - requirements.txt

# Create templates directory
mkdir templates
# Save index.html in the templates directory
"""
    story.append(Preformatted(install_code, code_style))
    
    story.append(Paragraph("Step 2: Create Virtual Environment", styles['Heading3']))
    venv_code = """
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate

# On macOS/Linux:
source venv/bin/activate
"""
    story.append(Preformatted(venv_code, code_style))
    
    story.append(Paragraph("Step 3: Install Dependencies", styles['Heading3']))
    deps_code = """
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
"""
    story.append(Preformatted(deps_code, code_style))
    
    # Configuration
    story.append(Paragraph("3. Configuration", styles['Heading2']))
    
    story.append(Paragraph("Jira API Token Setup", styles['Heading3']))
    config_text = """
    To use this application, you need a Jira API token:
    
    1. Log in to your Jira account
    2. Go to Account Settings → Security → API tokens
    3. Click "Create API token"
    4. Give it a descriptive name (e.g., "Analytics Dashboard")
    5. Copy the generated token (save it securely)
    
    Note: The token will only be shown once, so save it immediately.
    """
    story.append(Paragraph(config_text, styles['Normal']))
    
    # Running the Application
    story.append(Paragraph("4. Running the Application", styles['Heading2']))
    
    run_code = """
# Make sure virtual environment is activated
# Navigate to project directory
cd jira-analytics

# Run the application
python app.py

# The application will start on http://localhost:5000
# Open your web browser and navigate to this URL
"""
    story.append(Preformatted(run_code, code_style))
    
    # Using the Dashboard
    story.append(Paragraph("5. Using the Dashboard", styles['Heading2']))
    
    usage_text = """
    Once the application is running:
    
    1. Open http://localhost:5000 in your browser
    2. Fill in the configuration form:
       • Jira Server URL: Your Jira instance URL (e.g., https://company.atlassian.net)
       • Access Token: The API token you created
       • JQL Query: A JQL query to filter issues (e.g., "project = MYPROJECT")
       • Analysis Period: Choose 1, 2, 3 months, or 1 year
    
    3. Click "Analyze Data" to start the analysis
    4. Review the generated charts and metrics
    5. Download the PDF report if needed
    """
    story.append(Paragraph(usage_text, styles['Normal']))
    
    # Troubleshooting
    story.append(Paragraph("6. Troubleshooting", styles['Heading2']))
    
    trouble_text = """
    Common Issues and Solutions:
    
    Connection Errors:
    • Verify your Jira URL is correct
    • Check that your API token is valid
    • Ensure your Jira instance is accessible
    
    No Data Found:
    • Verify your JQL query returns results in Jira
    • Check the date range of your issues
    • Ensure issues have status change history
    
    Performance Issues:
    • Limit the number of issues with more specific JQL
    • Use shorter time periods for analysis
    • Ensure adequate system memory
    
    Chart Generation Errors:
    • Check that matplotlib dependencies are installed
    • Ensure sufficient disk space for temporary files
    • Verify all required Python packages are installed
    """
    story.append(Paragraph(trouble_text, styles['Normal']))
    
    # Development and Testing
    story.append(Paragraph("7. Development and Testing", styles['Heading2']))
    
    story.append(Paragraph("Running Tests", styles['Heading3']))
    test_code = """
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
pytest

# Run specific test file
pytest test_jira_client.py

# Run with coverage
pip install pytest-cov
pytest --cov=. --cov-report=html
"""
    story.append(Preformatted(test_code, code_style))
    
    story.append(Paragraph("Development Mode", styles['Heading3']))
    dev_code = """
# Run in development mode with auto-reload
export FLASK_ENV=development  # On Windows: set FLASK_ENV=development
python app.py

# Or use Flask's built-in development server
flask run --debug
"""
    story.append(Preformatted(dev_code, code_style))
    
    # Build PDF
    doc.build(story)
    print("Setup guide generated: Jira_Analytics_Setup_Guide.pdf")

if __name__ == "__main__":
    create_setup_guide()