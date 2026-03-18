"""
Unit tests for Initiative Viewer PDF Generator.

Tests cover:
- PDF generation with various data structures
- Risk color mapping
- Table styles
- Empty data handling
"""

import pytest
import sys
from pathlib import Path
import io

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.initiative_viewer.pdf_generator import InitiativeViewerPDFGenerator
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors


@pytest.fixture
def pdf_generator():
    """Create PDF generator instance."""
    return InitiativeViewerPDFGenerator("https://test.atlassian.net")


@pytest.fixture
def sample_initiative():
    """Sample initiative for testing."""
    return {
        'key': 'INIT-1',
        'summary': 'Test Initiative',
        'assignee': 'John Doe',
        'status': 'In Progress',
        'project_key': 'TEST',
        'risk_probability': 3,
        'features': [
            {
                'key': 'FEAT-1',
                'summary': 'Test Feature',
                'assignee': 'Jane Smith',
                'status': 'In Progress',
                'project_key': 'TEST',
                'sub_features': [
                    {
                        'key': 'SUB-1',
                        'summary': 'Test Sub-Feature',
                        'assignee': 'Bob Johnson',
                        'status': 'To Do',
                        'project_key': 'TEST',
                        'epics_by_area': {
                            'Area1': [
                                {
                                    'key': 'EPIC-1',
                                    'summary': 'Test Epic 1',
                                    'assignee': 'Alice Williams',
                                    'status': 'In Progress',
                                    'project_key': 'TEST',
                                    'risk_probability': 1
                                },
                                {
                                    'key': 'EPIC-2',
                                    'summary': 'Test Epic 2',
                                    'assignee': 'Charlie Brown',
                                    'status': 'Done',
                                    'project_key': 'TEST',
                                    'risk_probability': 5
                                }
                            ],
                            'Area2': [
                                {
                                    'key': 'EPIC-3',
                                    'summary': 'Test Epic 3',
                                    'assignee': 'David Lee',
                                    'status': 'To Do',
                                    'project_key': 'TEST',
                                    'risk_probability': None
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


# Initialization Tests

def test_pdf_generator_initialization():
    """Test PDF generator initialization."""
    generator = InitiativeViewerPDFGenerator("https://test.atlassian.net")
    assert generator.jira_base_url == "https://test.atlassian.net"


def test_pdf_generator_strips_trailing_slash():
    """Test that trailing slash is stripped from URL."""
    generator = InitiativeViewerPDFGenerator("https://test.atlassian.net/")
    assert generator.jira_base_url == "https://test.atlassian.net"


# Risk Color Mapping Tests

def test_get_risk_color_all_levels(pdf_generator):
    """Test risk color mapping for all levels."""
    # Test valid levels
    color_1 = pdf_generator._get_risk_color(1)
    assert color_1 is not None
    assert isinstance(color_1, colors.Color)
    
    color_3 = pdf_generator._get_risk_color(3)
    assert color_3 is not None
    
    color_5 = pdf_generator._get_risk_color(5)
    assert color_5 is not None
    
    # Test None
    color_none = pdf_generator._get_risk_color(None)
    assert color_none is None


def test_get_risk_text_all_levels(pdf_generator):
    """Test risk text mapping for all levels."""
    assert pdf_generator._get_risk_text(1) == 'Low'
    assert pdf_generator._get_risk_text(2) == 'Low-Med'
    assert pdf_generator._get_risk_text(3) == 'Medium'
    assert pdf_generator._get_risk_text(4) == 'Med-High'
    assert pdf_generator._get_risk_text(5) == 'High'
    assert pdf_generator._get_risk_text(None) == 'N/A'


# PDF Generation Tests

def test_generate_hierarchy_pdf_basic(pdf_generator, sample_initiative):
    """Test basic PDF generation."""
    output = io.BytesIO()
    
    try:
        pdf_generator.generate_hierarchy_pdf(
            initiatives=[sample_initiative],
            output_file=output,
            fix_version='PI 2025.1'
        )
        
        # Check that PDF was generated
        output.seek(0)
        pdf_content = output.read()
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF')
    except Exception as e:
        pytest.fail(f"PDF generation failed: {str(e)}")


def test_generate_hierarchy_pdf_portrait(pdf_generator, sample_initiative):
    """Test PDF generation with portrait orientation."""
    output = io.BytesIO()
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[sample_initiative],
        output_file=output,
        fix_version='PI 2025.1',
        page_size=letter
    )
    
    output.seek(0)
    assert len(output.read()) > 0


def test_generate_hierarchy_pdf_landscape(pdf_generator, sample_initiative):
    """Test PDF generation with landscape orientation."""
    output = io.BytesIO()
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[sample_initiative],
        output_file=output,
        fix_version='PI 2025.1',
        page_size=landscape(letter)
    )
    
    output.seek(0)
    assert len(output.read()) > 0


def test_generate_hierarchy_pdf_custom_title(pdf_generator, sample_initiative):
    """Test PDF generation with custom title."""
    output = io.BytesIO()
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[sample_initiative],
        output_file=output,
        fix_version='PI 2025.1',
        title='Custom Report Title'
    )
    
    output.seek(0)
    assert len(output.read()) > 0


def test_generate_hierarchy_pdf_multiple_initiatives(pdf_generator, sample_initiative):
    """Test PDF with multiple initiatives."""
    output = io.BytesIO()
    
    initiative_2 = sample_initiative.copy()
    initiative_2['key'] = 'INIT-2'
    initiative_2['summary'] = 'Second Initiative'
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[sample_initiative, initiative_2],
        output_file=output,
        fix_version='PI 2025.1'
    )
    
    output.seek(0)
    assert len(output.read()) > 0


def test_generate_hierarchy_pdf_empty_initiatives(pdf_generator):
    """Test PDF generation with empty initiatives list."""
    output = io.BytesIO()
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[],
        output_file=output,
        fix_version='PI 2025.1'
    )
    
    output.seek(0)
    assert len(output.read()) > 0


def test_generate_hierarchy_pdf_no_epics(pdf_generator):
    """Test PDF with initiative that has no epics."""
    output = io.BytesIO()
    
    initiative = {
        'key': 'INIT-1',
        'summary': 'Initiative without epics',
        'assignee': 'John Doe',
        'status': 'In Progress',
        'project_key': 'TEST',
        'features': []
    }
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[initiative],
        output_file=output,
        fix_version='PI 2025.1'
    )
    
    output.seek(0)
    assert len(output.read()) > 0


# Table Style Tests

def test_get_epic_table_style(pdf_generator, sample_initiative):
    """Test epic table style generation."""
    epics = sample_initiative['features'][0]['sub_features'][0]['epics_by_area']['Area1']
    
    style = pdf_generator._get_epic_table_style(epics)
    
    assert style is not None
    # Check that style commands were added
    assert len(style._cmds) > 0


def test_get_epic_table_style_with_mixed_risks(pdf_generator):
    """Test table style with mixed risk levels."""
    epics = [
        {'key': 'E-1', 'risk_probability': 1},
        {'key': 'E-2', 'risk_probability': 3},
        {'key': 'E-3', 'risk_probability': 5},
        {'key': 'E-4', 'risk_probability': None},
    ]
    
    style = pdf_generator._get_epic_table_style(epics)
    assert style is not None


# Section Building Tests

def test_build_initiative_section(pdf_generator, sample_initiative):
    """Test building initiative section."""
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    elements = pdf_generator._build_initiative_section(sample_initiative, styles)
    
    assert len(elements) > 0


def test_build_feature_section(pdf_generator, sample_initiative):
    """Test building feature section."""
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    feature = sample_initiative['features'][0]
    elements = pdf_generator._build_feature_section(feature, styles)
    
    assert len(elements) > 0


def test_build_sub_feature_section(pdf_generator, sample_initiative):
    """Test building sub-feature section."""
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    sub_feature = sample_initiative['features'][0]['sub_features'][0]
    elements = pdf_generator._build_sub_feature_section(sub_feature, styles)
    
    assert len(elements) > 0


# Edge Case Tests

def test_long_epic_summary(pdf_generator):
    """Test handling of very long epic summaries."""
    output = io.BytesIO()
    
    initiative = {
        'key': 'INIT-1',
        'summary': 'Test',
        'assignee': 'John',
        'status': 'Open',
        'project_key': 'TEST',
        'features': [{
            'key': 'F-1',
            'summary': 'Feature',
            'sub_features': [{
                'key': 'SF-1',
                'summary': 'Sub-Feature',
                'epics_by_area': {
                    'Area1': [{
                        'key': 'E-1',
                        'summary': 'A' * 200,  # Very long summary
                        'assignee': 'Test',
                        'status': 'Open',
                        'risk_probability': 3
                    }]
                }
            }]
        }]
    }
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[initiative],
        output_file=output,
        fix_version='PI 2025.1'
    )
    
    output.seek(0)
    assert len(output.read()) > 0


def test_special_characters_in_summary(pdf_generator):
    """Test handling of special characters in summaries."""
    output = io.BytesIO()
    
    initiative = {
        'key': 'INIT-1',
        'summary': 'Test & Special <chars> "quotes"',
        'assignee': 'O\'Brien',
        'status': 'In Progress',
        'project_key': 'TEST',
        'features': []
    }
    
    pdf_generator.generate_hierarchy_pdf(
        initiatives=[initiative],
        output_file=output,
        fix_version='PI 2025.1'
    )
    
    output.seek(0)
    assert len(output.read()) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
