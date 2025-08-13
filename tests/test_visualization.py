"""
Tests for Visualization module
"""

import pytest
import numpy as np
from visualization import VisualizationGenerator

class TestVisualizationGenerator:
    """Test suite for VisualizationGenerator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.viz_gen = VisualizationGenerator()
    
    def test_distribution_chart_creation(self):
        """Test distribution chart creation."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        chart = self.viz_gen._create_distribution_chart(
            data, "Test Distribution", "X Axis", "Y Axis"
        )
        
        assert chart.startswith("data:image/png;base64,")
        assert len(chart) > 100  # Should contain substantial base64 data
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_analysis = {
            'lead_times': [],
            'cycle_times': {},
            'status_durations': {},
            'metrics': {}
        }
        
        charts = self.viz_gen.generate_all_charts(empty_analysis)
        
        # Should not crash and return dict
        assert isinstance(charts, dict)