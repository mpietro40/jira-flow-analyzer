"""
Visualization Module
Generates charts and graphs for Jira analytics data.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats
import io
import base64
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Set style for better-looking plots
plt.style.use('default')
sns.set_theme()

class VisualizationGenerator:
    """
    Generates visualizations for Jira analytics data.
    
    This class creates various charts including histograms, box plots,
    and distribution plots for agile metrics analysis.
    """
    
    def __init__(self):
        """Initialize the visualization generator."""
        self.figure_size = (12, 8)
        self.dpi = 100
    
    def generate_all_charts(self, analysis_results: Dict) -> Dict:
        """
        Generate all charts for the analysis results.
        
        Args:
            analysis_results (Dict): Results from DataAnalyzer
            
        Returns:
            Dict: Dictionary containing base64-encoded chart images
        """
        charts = {}
        
        try:
            # Lead time distribution
            if analysis_results.get('lead_times'):
                charts['lead_time_distribution'] = self._create_distribution_chart(
                    analysis_results['lead_times'],
                    'Lead Time Distribution',
                    'Lead Time (Days)',
                    'Frequency'
                )
            
            # Cycle time charts
            if analysis_results.get('cycle_times'):
                charts['cycle_time_comparison'] = self._create_cycle_time_comparison(
                    analysis_results['cycle_times']
                )
            
            # Status duration box plots
            if analysis_results.get('status_durations'):
                charts['status_duration_boxplot'] = self._create_status_duration_boxplot(
                    analysis_results['status_durations']
                )
            
            # Lead time trend over time (if we have enough data)
            if analysis_results.get('lead_times') and len(analysis_results['lead_times']) > 10:
                charts['lead_time_trend'] = self._create_trend_chart(
                    analysis_results['lead_times']
                )
            
            # Summary metrics chart
            if analysis_results.get('metrics'):
                charts['metrics_summary'] = self._create_metrics_summary_chart(
                    analysis_results['metrics']
                )
            
        except Exception as e:
            logger.error(f"Chart generation error: {str(e)}")
            charts['error'] = str(e)
        
        return charts
    
    def _create_distribution_chart(self, data: List[float], title: str, 
                                 xlabel: str, ylabel: str) -> str:
        """
        Create a distribution chart with histogram and fitted normal curve.
        
        Args:
            data (List[float]): Data points
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            
        Returns:
            str: Base64-encoded chart image
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # Create histogram
        n_bins = min(30, max(10, len(data) // 4))
        counts, bins, patches = ax.hist(data, bins=n_bins, density=True, alpha=0.7, 
                                       color='skyblue', edgecolor='black')
        
        # Fit and plot normal distribution
        mu, std = stats.norm.fit(data)
        x = np.linspace(min(data), max(data), 100)
        y = stats.norm.pdf(x, mu, std)
        ax.plot(x, y, 'r-', linewidth=2, label=f'Normal Fit (μ={mu:.1f}, σ={std:.1f})')
        
        # Add statistics text
        stats_text = f'Mean: {np.mean(data):.1f}\nMedian: {np.median(data):.1f}\nStd: {np.std(data):.1f}'
        ax.text(0.75, 0.75, stats_text, transform=ax.transAxes, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_cycle_time_comparison(self, cycle_times: Dict[str, List[float]]) -> str:
        """
        Create a comparison chart for different cycle times.
        
        Args:
            cycle_times (Dict[str, List[float]]): Cycle time data by status
            
        Returns:
            str: Base64-encoded chart image
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), dpi=self.dpi)
        
        # Prepare data for box plot
        data_for_boxplot = []
        labels = []
        
        for status, times in cycle_times.items():
            if times and status != 'total':  # Exclude total from individual comparison
                data_for_boxplot.append(times)
                labels.append(status.replace('_', ' ').title())
        
        if data_for_boxplot:
            # Box plot
            box_plot = ax1.boxplot(data_for_boxplot, labels=labels, patch_artist=True)
            
            # Color the boxes
            colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']
            for patch, color in zip(box_plot['boxes'], colors[:len(box_plot['boxes'])]):
                patch.set_facecolor(color)
            
            ax1.set_title('Cycle Time Distribution by Status', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Time (Days)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
        
        # Bar chart for averages
        if cycle_times:
            status_names = []
            averages = []
            
            for status, times in cycle_times.items():
                if times:
                    status_names.append(status.replace('_', ' ').title())
                    averages.append(np.mean(times))
            
            bars = ax2.bar(status_names, averages, color=['skyblue', 'lightgreen', 'lightcoral', 'lightyellow'])
            ax2.set_title('Average Cycle Time by Status', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Average Time (Days)', fontsize=12)
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, avg in zip(bars, averages):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{avg:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_status_duration_boxplot(self, status_durations: Dict[str, List[float]]) -> str:
        """
        Create box plot for status durations.
        
        Args:
            status_durations (Dict[str, List[float]]): Status duration data
            
        Returns:
            str: Base64-encoded chart image
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # Prepare data
        data = []
        labels = []
        
        for status, durations in status_durations.items():
            if durations:
                data.append(durations)
                labels.append(status.replace('_', ' ').title())
        
        if data:
            # Create box plot
            box_plot = ax.boxplot(data, labels=labels, patch_artist=True, 
                                showmeans=True, meanline=True)
            
            # Customize colors
            colors = ['lightblue', 'lightgreen', 'lightcoral']
            for patch, color in zip(box_plot['boxes'], colors[:len(box_plot['boxes'])]):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            # Customize mean lines
            for mean_line in box_plot['means']:
                mean_line.set_color('red')
                mean_line.set_linewidth(2)
            
            ax.set_title('Time Spent in Each Status', fontsize=16, fontweight='bold')
            ax.set_ylabel('Duration (Days)', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Add legend
            ax.legend([box_plot['means'][0]], ['Mean'], loc='upper right')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_trend_chart(self, data: List[float]) -> str:
        """
        Create a trend chart showing data points over time.
        
        Args:
            data (List[float]): Time series data
            
        Returns:
            str: Base64-encoded chart image
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # Create trend line
        x = range(len(data))
        ax.plot(x, data, 'o-', color='blue', alpha=0.7, markersize=4)
        
        # Add trend line
        z = np.polyfit(x, data, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "r--", alpha=0.8, linewidth=2, label=f'Trend (slope: {z[0]:.2f})')
        
        # Add moving average
        if len(data) > 5:
            window_size = min(7, len(data) // 3)
            moving_avg = pd.Series(data).rolling(window=window_size, center=True).mean()
            ax.plot(x, moving_avg, 'g-', alpha=0.8, linewidth=2, label=f'Moving Average ({window_size})')
        
        ax.set_title('Lead Time Trend Analysis', fontsize=16, fontweight='bold')
        ax.set_xlabel('Issue Number (Chronological Order)', fontsize=12)
        ax.set_ylabel('Lead Time (Days)', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_metrics_summary_chart(self, metrics: Dict) -> str:
        """
        Create a summary chart showing key metrics.
        
        Args:
            metrics (Dict): Summary metrics
            
        Returns:
            str: Base64-encoded chart image
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), dpi=self.dpi)
        
        # Lead time metrics
        if 'lead_time' in metrics:
            lead_metrics = metrics['lead_time']
            categories = ['Average', 'Median', '85th %ile', '95th %ile']
            values = [lead_metrics.get('average', 0), lead_metrics.get('median', 0),
                     lead_metrics.get('p85', 0), lead_metrics.get('p95', 0)]
            
            bars1 = ax1.bar(categories, values, color='skyblue')
            ax1.set_title('Lead Time Metrics', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Days', fontsize=12)
            ax1.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar, value in zip(bars1, values):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{value:.1f}', ha='center', va='bottom')
        
        # Cycle time comparison
        cycle_averages = {}
        for key, value in metrics.items():
            if key.startswith('cycle_time_') and isinstance(value, dict):
                status = key.replace('cycle_time_', '').replace('_', ' ').title()
                cycle_averages[status] = value.get('average', 0)
        
        if cycle_averages:
            statuses = list(cycle_averages.keys())
            avg_times = list(cycle_averages.values())
            
            bars2 = ax2.bar(statuses, avg_times, color=['lightgreen', 'lightcoral', 'lightyellow'])
            ax2.set_title('Average Cycle Time by Status', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Days', fontsize=12)
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar, value in zip(bars2, avg_times):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{value:.1f}', ha='center', va='bottom')
        
        # Percentile comparison
        if 'lead_time' in metrics:
            lead_metrics = metrics['lead_time']
            percentiles = ['50th', '85th', '95th']
            perc_values = [lead_metrics.get('median', 0), lead_metrics.get('p85', 0),
                          lead_metrics.get('p95', 0)]
            
            bars3 = ax3.bar(percentiles, perc_values, color='lightpink')
            ax3.set_title('Lead Time Percentiles', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Days', fontsize=12)
            
            # Add value labels
            for bar, value in zip(bars3, perc_values):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{value:.1f}', ha='center', va='bottom')
        
        # Summary statistics table
        ax4.axis('tight')
        ax4.axis('off')
        
        # Create summary table
        table_data = []
        if 'lead_time' in metrics:
            lt = metrics['lead_time']
            table_data.append(['Lead Time Average', f"{lt.get('average', 0):.1f} days"])
            table_data.append(['Lead Time Median', f"{lt.get('median', 0):.1f} days"])
            table_data.append(['85th Percentile', f"{lt.get('p85', 0):.1f} days"])
            table_data.append(['95th Percentile', f"{lt.get('p95', 0):.1f} days"])
        
        if table_data:
            table = ax4.table(cellText=table_data,
                            colLabels=['Metric', 'Value'],
                            cellLoc='center',
                            loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1.2, 1.5)
            
            ax4.set_title('Summary Statistics', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """
        Convert matplotlib figure to base64 string.
        
        Args:
            fig: Matplotlib figure object
            
        Returns:
            str: Base64-encoded image
        """
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        
        img_str = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)  # Free memory
        
        return f"data:image/png;base64,{img_str}"