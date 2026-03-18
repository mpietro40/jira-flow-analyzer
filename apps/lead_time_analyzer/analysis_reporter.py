"""
Analysis Report Generator
Generates comprehensive reports explaining lead time metrics and identifying outliers.
"""

import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger('AnalysisReporter')

class AnalysisReporter:
    """Generates comprehensive analysis reports with statistical insights and outlier identification."""
    
    def generate_comprehensive_report(self, analysis_results: Dict) -> Dict:
        """
        Generate a comprehensive analysis report with statistical insights and outlier identification.
        
        Args:
            analysis_results (Dict): Analysis results from data analyzer
            
        Returns:
            Dict: Comprehensive report with insights and recommendations
        """
        report = {
            'statistical_analysis': self._analyze_distribution(analysis_results),
            'outlier_analysis': self._identify_outliers(analysis_results),
            'recommendations': self._generate_recommendations(analysis_results),
            'executive_summary': self._generate_executive_summary(analysis_results)
        }
        
        return report
    
    def _analyze_distribution(self, results: Dict) -> Dict:
        """Analyze the statistical distribution of lead times."""
        lead_times = results.get('lead_times', [])
        if not lead_times:
            return {'error': 'No lead time data available'}
        
        metrics = results.get('metrics', {}).get('lead_time', {})
        mean = metrics.get('average', 0)
        median = metrics.get('median', 0)
        p85 = metrics.get('p85', 0)
        p95 = metrics.get('p95', 0)
        
        std_dev = np.std(lead_times)
        coefficient_of_variation = std_dev / mean if mean > 0 else 0
        
        # Determine distribution type
        skewness = self._calculate_skewness(lead_times, mean, std_dev)
        distribution_type = self._classify_distribution(mean, median, std_dev)
        
        return {
            'mean': mean,
            'median': median,
            'std_dev': std_dev,
            'p85': p85,
            'p95': p95,
            'coefficient_of_variation': coefficient_of_variation,
            'skewness': skewness,
            'distribution_type': distribution_type,
            'interpretation': self._interpret_distribution(mean, median, std_dev, distribution_type)
        }
    
    def _identify_outliers(self, results: Dict) -> Dict:
        """Identify and analyze the top 5 outliers affecting lead time."""
        lead_times = results.get('lead_times', [])
        if not lead_times:
            return {
                'error': 'No lead time data available',
                'total_outliers': 0,
                'top_5_outliers': [],
                'outlier_impact': {'potential_improvement': 0, 'inflation_factor': 1}
            }
        
        # Get issue data for detailed analysis
        issues_data = results.get('issues_with_lead_times', [])
        
        # Calculate outlier threshold (typically 1.5 * IQR above Q3)
        q1 = np.percentile(lead_times, 25)
        q3 = np.percentile(lead_times, 75)
        iqr = q3 - q1
        outlier_threshold = q3 + 1.5 * iqr
        
        # Find outliers with issue details
        outlier_issues = []
        for i, lead_time in enumerate(lead_times):
            if lead_time > outlier_threshold:
                issue_info = issues_data[i] if i < len(issues_data) else {'key': f'Issue-{i+1}', 'summary': 'Unknown'}
                outlier_issues.append({
                    'lead_time': lead_time,
                    'key': issue_info.get('key', f'Issue-{i+1}'),
                    'summary': issue_info.get('summary', 'Unknown')[:50] + '...' if len(issue_info.get('summary', '')) > 50 else issue_info.get('summary', 'Unknown')
                })
        
        # Sort by lead time (highest first) and get top 5
        outlier_issues.sort(key=lambda x: x['lead_time'], reverse=True)
        top_5_outliers = outlier_issues[:5]
        
        return {
            'outlier_threshold': outlier_threshold,
            'total_outliers': len(outlier_issues),
            'top_5_outliers': [o['lead_time'] for o in top_5_outliers],
            'top_5_outlier_details': top_5_outliers,
            'outlier_impact': self._calculate_outlier_impact(lead_times, [o['lead_time'] for o in outlier_issues]),
            'outlier_analysis': self._analyze_outlier_patterns([o['lead_time'] for o in top_5_outliers], results)
        }
    
    def _generate_recommendations(self, results: Dict) -> List[Dict]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        distribution = self._analyze_distribution(results)
        outliers = self._identify_outliers(results)
        
        # Recommendation 1: Address outliers
        if outliers.get('total_outliers', 0) > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Outlier Management',
                'title': 'Focus on Eliminating Long-Tail Items',
                'description': f"You have {outliers['total_outliers']} outlier items taking longer than {outliers['outlier_threshold']:.1f} days. These items are inflating your average lead time.",
                'action': 'Investigate the top 5 longest items to identify common blockers, dependencies, or process issues.',
                'expected_impact': f"Eliminating outliers could reduce average lead time by {outliers['outlier_impact']['potential_improvement']:.1f} days"
            })
        
        # Recommendation 2: Process predictability
        if distribution.get('coefficient_of_variation', 0) > 1:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Process Stability',
                'title': 'Improve Process Predictability',
                'description': f"Your coefficient of variation is {distribution['coefficient_of_variation']:.2f}, indicating high unpredictability.",
                'action': 'Standardize work processes, implement WIP limits, and establish clear definition of done criteria.',
                'expected_impact': 'Reduced variability will make delivery dates more predictable'
            })
        
        # Recommendation 3: Use median for planning
        if distribution.get('mean', 0) > distribution.get('median', 0) * 1.5:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Planning & Estimation',
                'title': 'Use Median for Delivery Estimates',
                'description': f"Your median ({distribution['median']:.1f} days) is much lower than your mean ({distribution['mean']:.1f} days).",
                'action': f"Use the median ({distribution['median']:.1f} days) or 85th percentile ({distribution.get('p85', 0):.1f} days) for customer commitments instead of the average.",
                'expected_impact': 'More realistic delivery estimates and improved customer satisfaction'
            })
        
        return recommendations
    
    def _generate_executive_summary(self, results: Dict) -> str:
        """Generate executive summary of the analysis."""
        distribution = self._analyze_distribution(results)
        outliers = self._identify_outliers(results)
        total_issues = results.get('total_issues', 0)
        
        mean = distribution.get('mean', 0)
        median = distribution.get('median', 0)
        std_dev = distribution.get('std_dev', 0)
        
        summary = f"""
## Executive Summary: Lead Time Analysis

**Dataset:** {total_issues} issues analyzed
**Key Finding:** Your lead time distribution is {distribution.get('distribution_type', 'unknown')}

### Critical Insights:

1. **Typical vs Average Performance:**
   - Median (typical): {median:.1f} days
   - Mean (average): {mean:.1f} days
   - 50% of work completes in under {median:.1f} days, but the average is inflated by outliers

2. **Process Predictability:**
   - Standard deviation: {std_dev:.1f} days
   - Coefficient of variation: {distribution.get('coefficient_of_variation', 0):.2f}
   - {"HIGH VOLATILITY - Process is unpredictable" if distribution.get('coefficient_of_variation', 0) > 1 else "MODERATE VOLATILITY - Some predictability issues"}

3. **Outlier Impact:**
   - {outliers.get('total_outliers', 0)} items are statistical outliers (>{outliers.get('outlier_threshold', 0):.1f} days)
   - Top outlier: {outliers.get('top_5_outliers', [0])[0]:.1f if outliers.get('top_5_outliers') else 0:.1f} days
   - Outliers inflate average by {outliers.get('outlier_impact', {}).get('inflation_factor', 0):.1f}x

### Immediate Actions:
1. **Investigate the top 5 longest items** to identify systemic issues
2. **Use median ({median:.1f} days) for customer commitments** instead of average
3. **Focus on reducing variability** rather than just speed

### Bottom Line:
Your process delivers most work quickly ({median:.1f} days), but a few problematic items create unpredictability and inflate averages. Fix the outliers to achieve predictable delivery.
        """
        
        return summary.strip()
    
    def _calculate_skewness(self, data: List[float], mean: float, std_dev: float) -> float:
        """Calculate skewness of the distribution."""
        if std_dev == 0:
            return 0
        n = len(data)
        skewness = sum(((x - mean) / std_dev) ** 3 for x in data) / n
        return skewness
    
    def _classify_distribution(self, mean: float, median: float, std_dev: float) -> str:
        """Classify the type of distribution."""
        if std_dev > mean:
            return "Right-Skewed (High Variability)"
        elif mean > median * 1.2:
            return "Right-Skewed (Long Tail)"
        elif abs(mean - median) < 0.1 * mean:
            return "Approximately Normal"
        else:
            return "Skewed Distribution"
    
    def _interpret_distribution(self, mean: float, median: float, std_dev: float, dist_type: str) -> str:
        """Provide interpretation of the distribution."""
        if "Right-Skewed" in dist_type:
            return f"Your process has a 'long tail' of delayed items. Most work completes quickly (median: {median:.1f} days), but outliers inflate the average to {mean:.1f} days. Focus on eliminating the slowest items."
        elif "Normal" in dist_type:
            return f"Your process shows normal variation around {mean:.1f} days. This indicates a stable, predictable process."
        else:
            return f"Your process shows irregular patterns. The difference between median ({median:.1f}) and mean ({mean:.1f}) suggests some systematic issues."
    
    def _calculate_outlier_impact(self, all_times: List[float], outliers: List[float]) -> Dict:
        """Calculate the impact of outliers on overall metrics."""
        if not outliers:
            return {'potential_improvement': 0, 'inflation_factor': 1}
        
        current_mean = np.mean(all_times)
        without_outliers = [t for t in all_times if t not in outliers]
        
        if without_outliers:
            improved_mean = np.mean(without_outliers)
            potential_improvement = current_mean - improved_mean
            inflation_factor = current_mean / improved_mean
        else:
            potential_improvement = 0
            inflation_factor = 1
        
        return {
            'potential_improvement': potential_improvement,
            'inflation_factor': inflation_factor,
            'outlier_percentage': len(outliers) / len(all_times) * 100
        }
    
    def _analyze_outlier_patterns(self, top_outliers: List[float], results: Dict) -> Dict:
        """Analyze patterns in the top outliers."""
        if not top_outliers:
            return {
                'longest_item': 0,
                'outlier_range': 'No outliers found',
                'average_outlier_time': 0,
                'investigation_priority': 'No outliers to investigate'
            }
        
        return {
            'longest_item': max(top_outliers),
            'outlier_range': f"{min(top_outliers):.1f} - {max(top_outliers):.1f} days",
            'average_outlier_time': np.mean(top_outliers),
            'investigation_priority': "These items should be investigated first as they have the highest impact on team performance"
        }