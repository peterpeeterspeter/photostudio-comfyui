"""
Metrics Dashboard for Phase 2.1
Comparative reporting of ΔE, EdgeGate, and Semantic Score
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse


class MetricsDashboard:
    """
    Dashboard for visualizing and analyzing Phase 2.1 metrics
    """
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Define color scheme
        self.colors = {
            'excellent': '#2E8B57',  # Sea Green
            'good': '#32CD32',       # Lime Green
            'acceptable': '#FFD700',  # Gold
            'poor': '#FF6347',       # Tomato
            'critical': '#DC143C'    # Crimson
        }
        
        # Define thresholds
        self.thresholds = {
            'delta_e': {'excellent': 2.0, 'good': 4.0, 'acceptable': 6.0, 'poor': 10.0},
            'edge_gate': {'excellent': 0.9, 'good': 0.8, 'acceptable': 0.7, 'poor': 0.6},
            'semantic_score': {'excellent': 0.9, 'good': 0.8, 'acceptable': 0.7, 'poor': 0.6},
            'qa_total': {'excellent': 0.9, 'good': 0.8, 'acceptable': 0.7, 'poor': 0.6}
        }
    
    def load_results(self, pattern: str = "*.json") -> List[Dict]:
        """
        Load results from JSON files in the results directory.
        
        Args:
            pattern: File pattern to match (default: "*.json")
            
        Returns:
            List of loaded results
        """
        results = []
        
        for file_path in self.results_dir.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['file_name'] = file_path.name
                    data['timestamp'] = file_path.stat().st_mtime
                    results.append(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load {file_path}: {e}")
        
        return results
    
    def extract_metrics(self, results: List[Dict]) -> pd.DataFrame:
        """
        Extract metrics from results into a pandas DataFrame.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            DataFrame with extracted metrics
        """
        metrics_data = []
        
        for result in results:
            # Extract basic info
            row = {
                'file_name': result.get('file_name', 'unknown'),
                'timestamp': result.get('timestamp', 0),
                'schema_version': result.get('schema_version', 'unknown')
            }
            
            # Extract garment info
            garment = result.get('garment', {})
            row.update({
                'category': garment.get('category', 'unknown'),
                'color_hex': garment.get('color_hex', '#000000'),
                'pattern': garment.get('pattern', 'unknown'),
                'complexity_score': garment.get('complexity_score', 0.0),
                'transparency_level': garment.get('transparency_level', 0.0)
            })
            
            # Extract pre-analysis features
            pre_analysis = result.get('pre_analysis', {})
            row.update({
                'dominant_colors_count': len(pre_analysis.get('dominant_colors', [])),
                'pattern_complexity': pre_analysis.get('pattern_complexity', 'unknown'),
                'text_detected': pre_analysis.get('text_detected', False),
                'exposure': pre_analysis.get('exposure', 0.0),
                'contrast': pre_analysis.get('contrast', 0.0)
            })
            
            # Extract segmentation quality
            segmentation = result.get('segmentation', {})
            row.update({
                'mask_quality_score': segmentation.get('mask_quality_score', 0.0),
                'edge_alignment': segmentation.get('edge_alignment', 0.0),
                'mask_entropy': segmentation.get('mask_entropy', 0.0),
                'stability': segmentation.get('stability', 0.0),
                'parts_detected': segmentation.get('parts_detected', 0)
            })
            
            # Extract QA metrics
            qa_metrics = result.get('qa_metrics', {})
            row.update({
                'edge_gate': qa_metrics.get('edge_gate', 0.0),
                'background_gate': qa_metrics.get('background_gate', 0.0),
                'color_fidelity': qa_metrics.get('color_fidelity', 0.0),
                'semantic_alignment': qa_metrics.get('semantic_alignment', 0.0),
                'qa_total': qa_metrics.get('qa_total', 0.0),
                'passed': qa_metrics.get('passed', False)
            })
            
            # Extract individual quality gates
            individual_gates = qa_metrics.get('individual_gates', {})
            color_accuracy = individual_gates.get('color_accuracy', {})
            edge_quality = individual_gates.get('edge_quality', {})
            background_purity = individual_gates.get('background_purity', {})
            
            row.update({
                'delta_e': color_accuracy.get('delta_e', 0.0),
                'ssim_score': edge_quality.get('ssim_score', 0.0),
                'purity_score': background_purity.get('purity_score', 0.0)
            })
            
            # Extract part analysis
            parts = garment.get('parts', [])
            if parts:
                part_scores = [part.get('seam_quality', 0.0) for part in parts]
                row.update({
                    'avg_seam_quality': np.mean(part_scores),
                    'min_seam_quality': np.min(part_scores),
                    'max_seam_quality': np.max(part_scores),
                    'parts_count': len(parts)
                })
            else:
                row.update({
                    'avg_seam_quality': 0.0,
                    'min_seam_quality': 0.0,
                    'max_seam_quality': 0.0,
                    'parts_count': 0
                })
            
            metrics_data.append(row)
        
        return pd.DataFrame(metrics_data)
    
    def categorize_quality(self, value: float, metric: str) -> str:
        """
        Categorize a metric value into quality levels.
        
        Args:
            value: Metric value
            metric: Metric name
            
        Returns:
            Quality category
        """
        if metric not in self.thresholds:
            return 'unknown'
        
        thresholds = self.thresholds[metric]
        
        if value >= thresholds['excellent']:
            return 'excellent'
        elif value >= thresholds['good']:
            return 'good'
        elif value >= thresholds['acceptable']:
            return 'acceptable'
        elif value >= thresholds['poor']:
            return 'poor'
        else:
            return 'critical'
    
    def plot_metric_distribution(self, df: pd.DataFrame, metric: str, 
                                title: str = None, save_path: str = None):
        """
        Plot distribution of a metric with quality categories.
        
        Args:
            df: DataFrame with metrics
            metric: Metric column name
            title: Plot title
            save_path: Path to save plot
        """
        if metric not in df.columns:
            print(f"Warning: Metric '{metric}' not found in data")
            return
        
        # Create quality categories
        df[f'{metric}_category'] = df[metric].apply(
            lambda x: self.categorize_quality(x, metric)
        )
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Histogram
        ax1.hist(df[metric], bins=30, alpha=0.7, edgecolor='black')
        ax1.set_xlabel(metric.replace('_', ' ').title())
        ax1.set_ylabel('Frequency')
        ax1.set_title(f'Distribution of {metric.replace("_", " ").title()}')
        ax1.grid(True, alpha=0.3)
        
        # Add threshold lines
        if metric in self.thresholds:
            thresholds = self.thresholds[metric]
            for level, value in thresholds.items():
                ax1.axvline(value, color=self.colors.get(level, 'gray'), 
                           linestyle='--', alpha=0.7, label=f'{level.title()}: {value}')
            ax1.legend()
        
        # Quality categories pie chart
        category_counts = df[f'{metric}_category'].value_counts()
        colors_list = [self.colors.get(cat, 'gray') for cat in category_counts.index]
        
        ax2.pie(category_counts.values, labels=category_counts.index, 
                colors=colors_list, autopct='%1.1f%%', startangle=90)
        ax2.set_title(f'Quality Distribution - {metric.replace("_", " ").title()}')
        
        # Overall title
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        
        plt.show()
    
    def plot_correlation_matrix(self, df: pd.DataFrame, save_path: str = None):
        """
        Plot correlation matrix of key metrics.
        
        Args:
            df: DataFrame with metrics
            save_path: Path to save plot
        """
        # Select numeric columns for correlation
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Filter to key metrics
        key_metrics = [
            'complexity_score', 'transparency_level', 'exposure', 'contrast',
            'mask_quality_score', 'edge_alignment', 'mask_entropy', 'stability',
            'edge_gate', 'background_gate', 'color_fidelity', 'semantic_alignment',
            'qa_total', 'delta_e', 'ssim_score', 'purity_score',
            'avg_seam_quality', 'parts_count'
        ]
        
        correlation_cols = [col for col in key_metrics if col in numeric_cols]
        
        if not correlation_cols:
            print("Warning: No numeric metrics found for correlation analysis")
            return
        
        # Calculate correlation matrix
        corr_matrix = df[correlation_cols].corr()
        
        # Create heatmap
        plt.figure(figsize=(16, 12))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='RdBu_r', center=0,
                    square=True, fmt='.2f', cbar_kws={"shrink": .8})
        
        plt.title('Correlation Matrix of Key Metrics', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Correlation matrix saved to: {save_path}")
        
        plt.show()
    
    def plot_quality_trends(self, df: pd.DataFrame, save_path: str = None):
        """
        Plot quality trends over time.
        
        Args:
            df: DataFrame with metrics
            save_path: Path to save plot
        """
        if 'timestamp' not in df.columns:
            print("Warning: No timestamp data available for trend analysis")
            return
        
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Create quality categories for key metrics
        key_metrics = ['delta_e', 'edge_gate', 'semantic_alignment', 'qa_total']
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        
        for i, metric in enumerate(key_metrics):
            if metric not in df.columns:
                continue
            
            ax = axes[i]
            
            # Create quality categories
            df[f'{metric}_category'] = df[metric].apply(
                lambda x: self.categorize_quality(x, metric)
            )
            
            # Plot time series
            for category in ['excellent', 'good', 'acceptable', 'poor', 'critical']:
                category_data = df[df[f'{metric}_category'] == category]
                if not category_data.empty:
                    ax.scatter(category_data['datetime'], category_data[metric], 
                              label=category, color=self.colors.get(category, 'gray'), 
                              alpha=0.7, s=50)
            
            ax.set_xlabel('Time')
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_title(f'{metric.replace("_", " ").title()} Over Time')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Add threshold lines
            if metric in self.thresholds:
                thresholds = self.thresholds[metric]
                for level, value in thresholds.items():
                    ax.axhline(value, color=self.colors.get(level, 'gray'), 
                              linestyle='--', alpha=0.5)
        
        plt.suptitle('Quality Trends Over Time', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Quality trends saved to: {save_path}")
        
        plt.show()
    
    def generate_summary_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate a summary report of metrics.
        
        Args:
            df: DataFrame with metrics
            
        Returns:
            Summary report dictionary
        """
        if df.empty:
            return {"error": "No data available for summary"}
        
        summary = {
            "overview": {
                "total_samples": len(df),
                "date_range": {
                    "start": pd.to_datetime(df['timestamp'], unit='s').min().isoformat(),
                    "end": pd.to_datetime(df['timestamp'], unit='s').max().isoformat()
                },
                "categories": df['category'].value_counts().to_dict(),
                "patterns": df['pattern'].value_counts().to_dict()
            },
            "quality_metrics": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
        # Quality metrics summary
        quality_metrics = ['delta_e', 'edge_gate', 'semantic_alignment', 'qa_total']
        
        for metric in quality_metrics:
            if metric in df.columns:
                values = df[metric]
                summary["quality_metrics"][metric] = {
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "pass_rate": float((values >= self.thresholds[metric]['acceptable']).mean())
                }
                
                # Quality distribution
                categories = values.apply(lambda x: self.categorize_quality(x, metric))
                summary["quality_metrics"][metric]["distribution"] = categories.value_counts().to_dict()
        
        # Performance metrics
        performance_metrics = [
            'mask_quality_score', 'edge_alignment', 'mask_entropy', 'stability',
            'avg_seam_quality', 'parts_count'
        ]
        
        for metric in performance_metrics:
            if metric in df.columns:
                values = df[metric]
                summary["performance_metrics"][metric] = {
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "std": float(values.std())
                }
        
        # Generate recommendations
        if 'qa_total' in df.columns:
            qa_total = df['qa_total']
            if qa_total.mean() < 0.7:
                summary["recommendations"].append(
                    "Overall QA score is below 0.7. Consider improving segmentation quality or prompt engineering."
                )
            
            if 'delta_e' in df.columns:
                delta_e = df['delta_e']
                if delta_e.mean() > 5.0:
                    summary["recommendations"].append(
                        "Color accuracy (ΔE) is above 5.0. Consider improving color matching in the pipeline."
                    )
            
            if 'edge_gate' in df.columns:
                edge_gate = df['edge_gate']
                if edge_gate.mean() < 0.8:
                    summary["recommendations"].append(
                        "Edge quality is below 0.8. Consider improving edge detection and inpainting."
                    )
        
        return summary
    
    def create_dashboard(self, pattern: str = "*.json", output_dir: str = "dashboard_output"):
        """
        Create a complete metrics dashboard.
        
        Args:
            pattern: File pattern to match for results
            output_dir: Directory to save dashboard outputs
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        print("Loading results...")
        results = self.load_results(pattern)
        
        if not results:
            print("No results found. Please ensure JSON files are in the results directory.")
            return
        
        print(f"Loaded {len(results)} results")
        
        print("Extracting metrics...")
        df = self.extract_metrics(results)
        
        print("Generating summary report...")
        summary = self.generate_summary_report(df)
        
        # Save summary report
        summary_path = output_dir / "summary_report.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary report saved to: {summary_path}")
        
        # Create plots
        print("Creating metric distribution plots...")
        key_metrics = ['delta_e', 'edge_gate', 'semantic_alignment', 'qa_total']
        
        for metric in key_metrics:
            if metric in df.columns:
                plot_path = output_dir / f"{metric}_distribution.png"
                self.plot_metric_distribution(df, metric, save_path=str(plot_path))
        
        print("Creating correlation matrix...")
        corr_path = output_dir / "correlation_matrix.png"
        self.plot_correlation_matrix(df, save_path=str(corr_path))
        
        print("Creating quality trends...")
        trends_path = output_dir / "quality_trends.png"
        self.plot_quality_trends(df, save_path=str(trends_path))
        
        # Save raw data
        data_path = output_dir / "metrics_data.csv"
        df.to_csv(data_path, index=False)
        print(f"Raw metrics data saved to: {data_path}")
        
        print(f"\nDashboard complete! Outputs saved to: {output_dir}")
        
        # Print summary
        print("\n" + "="*50)
        print("SUMMARY REPORT")
        print("="*50)
        
        print(f"Total Samples: {summary['overview']['total_samples']}")
        print(f"Date Range: {summary['overview']['date_range']['start']} to {summary['overview']['date_range']['end']}")
        
        print("\nQuality Metrics:")
        for metric, stats in summary['quality_metrics'].items():
            print(f"  {metric}:")
            print(f"    Mean: {stats['mean']:.3f}")
            print(f"    Pass Rate: {stats['pass_rate']:.1%}")
            print(f"    Distribution: {stats['distribution']}")
        
        if summary['recommendations']:
            print("\nRecommendations:")
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"  {i}. {rec}")


def main():
    """Command line interface for metrics dashboard"""
    parser = argparse.ArgumentParser(description='Phase 2.1 Metrics Dashboard')
    parser.add_argument('--results-dir', default='results',
                       help='Directory containing result JSON files')
    parser.add_argument('--pattern', default='*.json',
                       help='File pattern to match for results')
    parser.add_argument('--output-dir', default='dashboard_output',
                       help='Directory to save dashboard outputs')
    parser.add_argument('--metric', choices=['delta_e', 'edge_gate', 'semantic_alignment', 'qa_total'],
                       help='Plot specific metric distribution')
    
    args = parser.parse_args()
    
    dashboard = MetricsDashboard(args.results_dir)
    
    if args.metric:
        # Plot specific metric
        results = dashboard.load_results(args.pattern)
        if results:
            df = dashboard.extract_metrics(results)
            dashboard.plot_metric_distribution(df, args.metric)
        else:
            print("No results found.")
    else:
        # Create complete dashboard
        dashboard.create_dashboard(args.pattern, args.output_dir)


if __name__ == "__main__":
    main()
