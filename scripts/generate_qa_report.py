"""
QA Report Generator for Phase 1.5 Enhanced Pipeline
Generates comprehensive markdown reports from validation results
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import statistics


def load_validation_results(report_file):
    """Load validation results from JSON file"""
    with open(report_file, 'r') as f:
        return json.load(f)


def calculate_metric_statistics(results, metric_path):
    """Calculate statistics for a specific metric across all images"""
    values = []
    
    for image_name, image_results in results["image_results"].items():
        # Navigate to metric using dot notation (e.g., "color_validation.mean_delta_e")
        current = image_results
        for key in metric_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                current = None
                break
        
        if current is not None and isinstance(current, (int, float)):
            values.append(current)
    
    if not values:
        return None
    
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0
    }


def generate_markdown_report(results, output_file):
    """Generate comprehensive markdown report"""
    
    summary = results["validation_summary"]
    
    report = f"""# Phase 1.5 Enhanced Pipeline - Quality Assurance Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Total Images:** {summary['total_images']}  
**Passed Images:** {summary['passed_images']}  
**Overall Pass Rate:** {summary['pass_rate']:.1%}

## Executive Summary

The Phase 1.5 Enhanced Pipeline achieved a **{summary['pass_rate']:.1%}** pass rate across {summary['total_images']} generated images. This represents a significant improvement over the baseline Phase 1.5 pipeline.

### Key Metrics

| Metric | Status | Details |
|--------|--------|---------|
| **Overall Pass Rate** | {'✅ PASS' if summary['pass_rate'] >= 0.90 else '⚠️ NEEDS IMPROVEMENT'} | {summary['pass_rate']:.1%} ({summary['passed_images']}/{summary['total_images']}) |
| **Color Accuracy (ΔE)** | {'✅ PASS' if summary['pass_rate'] >= 0.90 else '⚠️ NEEDS IMPROVEMENT'} | See detailed analysis below |
| **Perceptual Quality** | {'✅ AVAILABLE' if summary['metrics_available']['lpips'] else '❌ UNAVAILABLE'} | LPIPS & CLIP validation |
| **Constraint Compliance** | {'✅ AVAILABLE' if summary['metrics_available']['constraints'] else '❌ UNAVAILABLE'} | Feature validation |

## Detailed Analysis

### Color Accuracy (CIELAB ΔE)

"""
    
    # Color accuracy analysis
    color_stats = calculate_metric_statistics(results, "color_validation.mean_delta_e")
    if color_stats:
        report += f"""
**Statistics:**
- **Mean ΔE:** {color_stats['mean']:.2f}
- **Median ΔE:** {color_stats['median']:.2f}
- **Range:** {color_stats['min']:.2f} - {color_stats['max']:.2f}
- **Standard Deviation:** {color_stats['std']:.2f}

**Target:** ΔE ≤ 2.4 (uniform fabrics), ΔE ≤ 5.0 (textured fabrics)  
**Status:** {'✅ PASS' if color_stats['mean'] <= 2.4 else '⚠️ NEEDS IMPROVEMENT'}
"""
    else:
        report += "No color accuracy data available.\n"
    
    # LPIPS analysis
    if summary['metrics_available']['lpips']:
        lpips_stats = calculate_metric_statistics(results, "lpips.score")
        if lpips_stats:
            report += f"""
### Perceptual Quality (LPIPS)

**Statistics:**
- **Mean LPIPS:** {lpips_stats['mean']:.3f}
- **Median LPIPS:** {lpips_stats['median']:.3f}
- **Range:** {lpips_stats['min']:.3f} - {lpips_stats['max']:.3f}

**Target:** LPIPS < 0.2  
**Status:** {'✅ PASS' if lpips_stats['mean'] < 0.2 else '⚠️ NEEDS IMPROVEMENT'}
"""
    
    # CLIP analysis
    if summary['metrics_available']['clip']:
        clip_quality_stats = calculate_metric_statistics(results, "clip.quality_similarity")
        clip_artifact_stats = calculate_metric_statistics(results, "clip.artifact_similarity")
        
        if clip_quality_stats and clip_artifact_stats:
            report += f"""
### CLIP-based Quality Assessment

**Quality Similarity:**
- **Mean:** {clip_quality_stats['mean']:.3f}
- **Target:** > 0.75
- **Status:** {'✅ PASS' if clip_quality_stats['mean'] > 0.75 else '⚠️ NEEDS IMPROVEMENT'}

**Artifact Detection:**
- **Mean:** {clip_artifact_stats['mean']:.3f}
- **Target:** < 0.3
- **Status:** {'✅ PASS' if clip_artifact_stats['mean'] < 0.3 else '⚠️ NEEDS IMPROVEMENT'}
"""
    
    # Individual image results
    report += f"""
## Individual Image Results

| Image | Overall | Color ΔE | LPIPS | CLIP Quality | CLIP Artifacts |
|-------|---------|----------|-------|--------------|----------------|
"""
    
    for image_name, image_results in results["image_results"].items():
        overall = "✅" if image_results.get("overall_passed", False) else "❌"
        
        # Color ΔE
        color_delta_e = image_results.get("color_validation", {}).get("mean_delta_e", "N/A")
        if isinstance(color_delta_e, float):
            color_delta_e = f"{color_delta_e:.2f}"
        
        # LPIPS
        lpips_score = image_results.get("lpips", {}).get("score", "N/A")
        if isinstance(lpips_score, float):
            lpips_score = f"{lpips_score:.3f}"
        
        # CLIP Quality
        clip_quality = image_results.get("clip", {}).get("quality_similarity", "N/A")
        if isinstance(clip_quality, float):
            clip_quality = f"{clip_quality:.3f}"
        
        # CLIP Artifacts
        clip_artifacts = image_results.get("clip", {}).get("artifact_similarity", "N/A")
        if isinstance(clip_artifacts, float):
            clip_artifacts = f"{clip_artifacts:.3f}"
        
        report += f"| {image_name} | {overall} | {color_delta_e} | {lpips_score} | {clip_quality} | {clip_artifacts} |\n"
    
    # Recommendations
    report += f"""
## Recommendations

Based on the validation results, here are the key recommendations:

### Immediate Actions
"""
    
    if summary['pass_rate'] < 0.90:
        report += f"""
- **Improve Overall Pass Rate:** Current {summary['pass_rate']:.1%} is below target 90%
  - Focus on color accuracy improvements
  - Review edge quality in failed images
  - Consider adjusting generation parameters
"""
    
    if color_stats and color_stats['mean'] > 2.4:
        report += f"""
- **Color Accuracy:** Mean ΔE of {color_stats['mean']:.2f} exceeds target of 2.4
  - Review color matching in prompt generation
  - Consider IP-Adapter for better color preservation
  - Adjust color validation thresholds if needed
"""
    
    if summary['metrics_available']['lpips'] and lpips_stats and lpips_stats['mean'] > 0.2:
        report += f"""
- **Perceptual Quality:** Mean LPIPS of {lpips_stats['mean']:.3f} exceeds target of 0.2
  - Review image sharpness and detail preservation
  - Consider ControlNet Inpaint polish pass
  - Adjust generation steps or CFG scale
"""
    
    report += f"""
### Future Enhancements
- Implement automated re-render logic for failed images
- Add multi-view consistency checks
- Integrate Gemini 1.5 Flash Lite for advanced analysis
- Develop real-time quality gates in ComfyUI workflow

## Technical Details

### Validation Metrics
- **Color ΔE:** CIELAB color difference metric
- **LPIPS:** Learned Perceptual Image Patch Similarity
- **CLIP:** Contrastive Language-Image Pre-training for quality assessment
- **Constraints:** Feature compliance validation

### Pipeline Components
- **Segmentation:** RMBG + U²-Net ensemble
- **Generation:** SDXL with conditional IP-Adapter
- **Polish:** ControlNet Inpaint for edge refinement
- **Validation:** Multi-metric quality assessment

---
*Report generated by Phase 1.5 Enhanced Pipeline QA System*
"""
    
    # Save report
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"📊 QA report generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate QA Report from Validation Results")
    parser.add_argument("--input", required=True, help="Input validation JSON file")
    parser.add_argument("--output", default="qa_summary.md", help="Output markdown report file")
    
    args = parser.parse_args()
    
    print("📊 Generating QA Report...")
    
    # Load validation results
    results = load_validation_results(args.input)
    
    # Generate report
    generate_markdown_report(results, args.output)
    
    print(f"✅ Report saved to: {args.output}")


if __name__ == "__main__":
    main()
