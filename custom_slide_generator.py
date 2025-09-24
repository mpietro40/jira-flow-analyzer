"""
Custom Slide Generator
Creates PDF presentations from JSON configuration with custom backgrounds and content.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import json
import os
import logging
from datetime import datetime
from io import BytesIO

logger = logging.getLogger('CustomSlideGenerator')

class CustomSlideGenerator:
    """
    Generates custom PDF presentations from JSON configuration.
    """
    
    def __init__(self):
        """Initialize the custom slide generator."""
        self.page_width, self.page_height = landscape(A4)
        self.doc_folder = os.path.join(os.path.dirname(__file__), 'doc')
        self.images_folder = os.path.join(self.doc_folder, 'images')
        
        # Create styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=36,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=24,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        self.content_style = ParagraphStyle(
            'CustomContent',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=12,
            leftIndent=50
        )
        
        self.footer_style = ParagraphStyle(
            'CustomFooter',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.white,
            alignment=TA_CENTER
        )
    
    def load_config(self, config_file: str = 'custom_slides.json') -> dict:
        """
        Load slide configuration from JSON file.
        
        Args:
            config_file (str): Name of the JSON config file
            
        Returns:
            dict: Configuration data
        """
        config_path = os.path.join(self.doc_folder, config_file)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"📋 Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"🚩 Failed to load config: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration if file loading fails."""
        return {
            "presentation": {
                "title": "Custom Presentation",
                "author": "Pietro Maffi",
                "date": "2025"
            },
            "slides": [
                {
                    "slide_number": 1,
                    "background_image": "slide_1.png",
                    "title": "Default Slide",
                    "subtitle": "Configuration not found",
                    "content": ["● Please check custom_slides.json"],
                    "footer": "Default Configuration"
                }
            ]
        }
    
    def generate_presentation(self, config_file: str = 'custom_slides.json') -> BytesIO:
        """
        Generate custom presentation from JSON configuration.
        
        Args:
            config_file (str): Name of the JSON config file
            
        Returns:
            BytesIO: PDF content as bytes
        """
        config = self.load_config(config_file)
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create custom canvas for background handling
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        slides = config.get('slides', [])
        logger.info(f"📊 Generating presentation with {len(slides)} slides")
        
        for slide_data in slides:
            self._create_slide(c, slide_data)
            c.showPage()
        
        c.save()
        buffer.seek(0)
        
        logger.info("✅ Custom presentation generated successfully")
        return buffer
    
    def _create_slide(self, canvas_obj, slide_data: dict):
        """
        Create a single slide with background and content.
        
        Args:
            canvas_obj: ReportLab canvas object
            slide_data (dict): Slide configuration data
        """
        # Add background image
        self._add_background(canvas_obj, slide_data.get('background_image', 'slide_1.png'))
        
        # Get font color for this slide
        font_color = slide_data.get('font_color', '#FFFFFF')
        text_color = colors.HexColor(font_color)
        
        # Add title
        title = slide_data.get('title', '')
        if title:
            canvas_obj.setFont("Helvetica-Bold", 36)
            canvas_obj.setFillColor(text_color)
            text_width = canvas_obj.stringWidth(title, "Helvetica-Bold", 36)
            canvas_obj.drawString((self.page_width - text_width) / 2, self.page_height - 150, title)
        
        # Add subtitle
        subtitle = slide_data.get('subtitle', '')
        if subtitle:
            canvas_obj.setFont("Helvetica", 24)
            canvas_obj.setFillColor(text_color)
            text_width = canvas_obj.stringWidth(subtitle, "Helvetica", 24)
            canvas_obj.drawString((self.page_width - text_width) / 2, self.page_height - 200, subtitle)
        
        # Add content
        content = slide_data.get('content', [])
        if content:
            canvas_obj.setFont("Helvetica", 18)
            canvas_obj.setFillColor(text_color)
            
            y_position = self.page_height - 280
            for item in content:
                # Replace placeholders
                item = item.replace('{current_date}', datetime.now().strftime('%Y-%m-%d'))
                canvas_obj.drawString(100, y_position, item)
                y_position -= 30
        
        # Add footer
        footer = slide_data.get('footer', '')
        if footer:
            footer = footer.replace('{current_date}', datetime.now().strftime('%Y-%m-%d'))
            canvas_obj.setFont("Helvetica", 12)
            canvas_obj.setFillColor(text_color)
            text_width = canvas_obj.stringWidth(footer, "Helvetica", 12)
            canvas_obj.drawString((self.page_width - text_width) / 2, 50, footer)
    
    def _add_background(self, canvas_obj, background_image: str):
        """
        Add background image to slide.
        
        Args:
            canvas_obj: ReportLab canvas object
            background_image (str): Background image filename
        """
        try:
            image_path = os.path.join(self.images_folder, background_image)
            
            if os.path.exists(image_path):
                canvas_obj.drawImage(
                    image_path,
                    0, 0,
                    width=self.page_width,
                    height=self.page_height,
                    preserveAspectRatio=False
                )
            else:
                # Fallback: solid color background
                canvas_obj.setFillColor(colors.HexColor('#2c3e50'))
                canvas_obj.rect(0, 0, self.page_width, self.page_height, fill=1)
                logger.warning(f"⚠️ Background image not found: {image_path}")
        
        except Exception as e:
            # Fallback: solid color background
            canvas_obj.setFillColor(colors.HexColor('#2c3e50'))
            canvas_obj.rect(0, 0, self.page_width, self.page_height, fill=1)
            logger.warning(f"⚠️ Failed to load background: {str(e)}")
    
    def save_presentation(self, output_filename: str = None, config_file: str = 'custom_slides.json') -> str:
        """
        Generate and save presentation to file.
        
        Args:
            output_filename (str): Output filename (optional)
            config_file (str): JSON config file name
            
        Returns:
            str: Path to saved file
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"Custom_Presentation_{timestamp}.pdf"
        
        output_path = os.path.join(self.doc_folder, output_filename)
        
        # Generate presentation
        pdf_buffer = self.generate_presentation(config_file)
        
        # Save to file
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        logger.info(f"💾 Presentation saved to: {output_path}")
        return output_path