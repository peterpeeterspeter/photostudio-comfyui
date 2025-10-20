# Phase 2.1 Implementation Guide

## Overview

Phase 2.1 implements targeted refinements to the Photostudio.io ComfyUI Ghost-Mannequin Pipeline, focusing on multimodal, research-backed "truth alignment" principles. This phase enhances the pipeline with pre-analysis features, mask quality scoring, dynamic prompts, semantic QA, and comprehensive metrics reporting.

## Key Enhancements

### 1. Pre-Analysis Layer
- **Color Palette Extraction**: K-means clustering for dominant color detection
- **Pattern Complexity**: FFT-based analysis for texture complexity scoring
- **OCR Text Detection**: Lightweight text region detection using PaddleOCR
- **Exposure/Contrast Metrics**: Global image quality assessment

### 2. Mask Quality Scoring
- **Edge Alignment**: Sobel edge detection overlap scoring
- **Mask Entropy**: Segmentation uncertainty quantification
- **Morphological Stability**: IoU-based stability across threshold variations
- **Ensemble Weighting**: RMBG + U²-Net contribution analysis

### 3. Dynamic Prompts Generation
- **Context-Weighted Prompts**: Facts V3.1-driven part segmentation prompts
- **Risk Zone Awareness**: Button overlap and transparency handling
- **Complexity Adaptation**: Part count scaling based on garment complexity
- **Interior Visibility**: Dynamic part inclusion for high-visibility garments

### 4. Semantic QA Verification
- **Gemini Re-Analysis**: AI-driven semantic alignment verification
- **Color ΔE Calculation**: CIELAB color difference measurement
- **Pattern Similarity**: Fuzzy pattern matching
- **Category Alignment**: Garment category consistency checking
- **Auto Re-render Logic**: Threshold-based quality control

### 5. Enhanced Facts Schema (V3.2)
- **Pre-Analysis Integration**: Context features in part analysis
- **Segmentation Metrics**: Mask quality and ensemble weights
- **QA Metrics**: Hierarchical quality scoring
- **Schema Validation**: JSON schema validation with custom rules

### 6. Hierarchical QA Scoring
- **Research-Based Weights**: Edge (40%), Background (30%), Color (20%), Semantic (10%)
- **Weighted Aggregation**: Individual metric combination
- **Pass/Fail Logic**: Configurable threshold-based decisions
- **Recommendation Engine**: Accept/re-render suggestions

## Implementation Details

### PreAnalysisNode

```python
# Key Features
- Color palette extraction (K-means clustering)
- FFT-based pattern complexity analysis
- OCR text detection (PaddleOCR integration)
- Exposure and contrast computation
- Debug visualization generation

# Input/Output
Input: IMAGE tensor
Output: pre_features_json (STRING), debug_image (IMAGE)

# Parameters
- n_color_clusters: Number of dominant colors to extract
- pattern_threshold: FFT complexity threshold
- enable_ocr: Enable/disable text detection
```

### AdvancedGarmentSegmentation (Enhanced)

```python
# New Features
- Mask quality scoring (edge alignment, entropy, stability)
- Ensemble weight calculation (RMBG vs U²-Net)
- Quality metrics JSON output
- Confidence scoring

# Input/Output
Input: IMAGE, rmbg_threshold, u2net_threshold, use_human_subtract, mask_blur, edge_feather
Output: garment_only (IMAGE), garment_mask (MASK), confidence (FLOAT), quality_metrics_json (STRING)

# Quality Metrics
- mask_quality_score: Overall mask quality (0.0-1.0)
- edge_alignment: Edge detection overlap score
- mask_entropy: Segmentation uncertainty measure
- stability: Morphological stability across thresholds
- mask_weights: RMBG/U²-Net contribution weights
```

### GarmentPartSegmentation (Enhanced)

```python
# New Features
- Dynamic prompts generation from Facts V3.1
- Context-weighted part selection
- Risk zone awareness
- Complexity-based part scaling

# Dynamic Prompt Logic
- High interior visibility → Add cuff, inner_collar
- Button overlap risk → Add placket
- High complexity → Add seam, pocket, button
- High transparency → Simplify to structural elements

# Input/Output
Input: IMAGE, garment_mask, segmentation_mode, min_parts_for_dino, confidence_threshold, facts_json (optional), part_prompts (optional)
Output: parts_json (STRING), parts_overlay (IMAGE)
```

### SemanticQANode

```python
# Key Features
- Gemini-based semantic alignment verification
- Color ΔE calculation (CIELAB)
- Pattern similarity detection
- Category alignment checking
- Auto re-render logic

# Input/Output
Input: rendered_image (IMAGE), original_facts_json (STRING), alignment_threshold (FLOAT), enable_auto_rerender (BOOLEAN)
Output: semantic_alignment_score (FLOAT), gemini_re_analysis_json (STRING), qa_report_json (STRING), should_rerender (BOOLEAN)

# Alignment Computation
- Category match: Exact string comparison
- Color match: ΔE color difference
- Pattern match: Fuzzy string matching
- Weighted average of all metrics
```

### Enhanced Gemini Part Analyzer

```python
# New Features
- Pre-analysis context injection
- Enhanced prompt templates
- Context-aware fallback analysis
- Pre-analysis feature utilization

# Context Integration
- Dominant colors → Part color analysis
- Pattern complexity → Risk score adjustment
- Text detection → Analysis method selection
- Exposure/contrast → Condition assessment
```

### Quality Validator (Enhanced)

```python
# New Features
- Hierarchical QA scoring
- Research-based weight system
- Weighted metric aggregation
- Pass/fail recommendation logic

# Weight System
- Edge quality: 40% (most critical for ghost mannequin)
- Background purity: 30% (second most important)
- Color fidelity: 20% (important but less critical)
- Semantic alignment: 10% (least critical but valuable)

# QA Total Calculation
qa_total = 0.4 * edge_gate + 0.3 * bg_gate + 0.2 * color_fidelity + 0.1 * semantic_alignment
```

## Facts Schema V3.2

### New Fields

```json
{
  "pre_analysis": {
    "dominant_colors": ["#1A2B3C", "#C8BFC0"],
    "pattern_complexity": "high|medium|low",
    "text_detected": true,
    "text_boxes": [[x1, y1, x2, y2]],
    "exposure": 0.81,
    "contrast": 0.65
  },
  "segmentation": {
    "mask_quality_score": 0.93,
    "edge_alignment": 0.95,
    "mask_entropy": 0.90,
    "stability": 0.94,
    "mask_weights": {
      "rmbg": 0.4,
      "u2net": 0.6
    }
  },
  "qa_metrics": {
    "edge_gate": 0.88,
    "background_gate": 0.95,
    "color_fidelity": 0.90,
    "semantic_alignment": 0.92,
    "qa_total": 0.91,
    "weights": {
      "edge": 0.4,
      "background": 0.3,
      "color": 0.2,
      "semantic": 0.1
    },
    "individual_scores": {
      "edge_weighted": 0.352,
      "background_weighted": 0.285,
      "color_weighted": 0.18,
      "semantic_weighted": 0.092
    },
    "pass_threshold": 0.85,
    "passed": true,
    "recommendation": "accept|re-render"
  }
}
```

## Testing Framework

### Unit Tests

1. **Mask Quality Tests** (`tests/test_mask_quality.py`)
   - Edge alignment calculation
   - Mask entropy computation
   - Morphological stability
   - Integration testing
   - Error handling

2. **Pre-Analysis Tests** (`tests/test_pre_analysis.py`)
   - Color palette extraction
   - Pattern complexity analysis
   - OCR text detection
   - Exposure/contrast computation
   - Full pipeline integration

3. **Semantic QA Tests** (`tests/test_semantic_qa.py`)
   - Color ΔE calculation
   - Pattern similarity detection
   - Category alignment
   - Gemini integration
   - Fallback analysis

### Integration Tests

4. **Phase 2.1 Integration** (`tests/test_phase2_1_integration.py`)
   - Complete pipeline testing
   - Data flow verification
   - Performance benchmarking
   - Error handling across components

### Schema Validation

5. **Schema Validator** (`facts/validate_schema.py`)
   - V3.1 and V3.2 schema validation
   - Custom validation rules
   - Batch validation support
   - Command-line interface

## Metrics Dashboard

### Features

- **Metric Distribution Plots**: Histograms and quality category pie charts
- **Correlation Matrix**: Heatmap of metric relationships
- **Quality Trends**: Time-series analysis of quality metrics
- **Summary Reports**: Comprehensive quality analysis
- **Recommendations**: Automated improvement suggestions

### Usage

```bash
# Create complete dashboard
python scripts/metrics_dashboard.py --results-dir results --output-dir dashboard_output

# Plot specific metric
python scripts/metrics_dashboard.py --metric delta_e

# Custom file pattern
python scripts/metrics_dashboard.py --pattern "phase2_1_*.json"
```

### Output Files

- `summary_report.json`: Comprehensive quality analysis
- `metrics_data.csv`: Raw metrics data
- `*_distribution.png`: Individual metric distributions
- `correlation_matrix.png`: Metric correlation heatmap
- `quality_trends.png`: Time-series quality trends

## Dependencies

### New Dependencies

```bash
pip install paddleocr scikit-learn jsonschema matplotlib seaborn pandas
```

### Key Libraries

- **PaddleOCR**: Text detection and recognition
- **scikit-learn**: K-means clustering for color extraction
- **jsonschema**: Schema validation
- **matplotlib/seaborn**: Visualization and plotting
- **pandas**: Data analysis and manipulation

## Performance Characteristics

### Expected Performance

- **Pre-Analysis**: < 5 seconds per image
- **Segmentation**: < 10 seconds per image
- **Semantic QA**: < 3 seconds per image
- **Total Pipeline**: < 20 seconds per image

### Quality Targets

- **Edge Gate**: > 0.8 (80% pass rate)
- **Background Gate**: > 0.95 (95% pass rate)
- **Color Fidelity**: ΔE < 4.0 (80% pass rate)
- **Semantic Alignment**: > 0.7 (70% pass rate)
- **Overall QA**: > 0.85 (85% pass rate)

## Integration with Existing Pipeline

### Backward Compatibility

- All enhancements are backward compatible
- Existing Facts V3.1 data works with V3.2 schema
- Fallback mechanisms for missing components
- Graceful degradation when services unavailable

### Workflow Integration

1. **Pre-Analysis**: Runs before segmentation
2. **Enhanced Segmentation**: Includes quality scoring
3. **Dynamic Prompts**: Uses pre-analysis context
4. **Semantic QA**: Runs after generation
5. **Hierarchical QA**: Final quality assessment

### Configuration

```yaml
# Example configuration
phase2_1:
  pre_analysis:
    n_color_clusters: 5
    pattern_threshold: 0.3
    enable_ocr: true
  
  segmentation:
    rmbg_threshold: 0.32
    u2net_threshold: 0.35
    use_human_subtract: true
    mask_blur: 3
    edge_feather: 4
  
  semantic_qa:
    alignment_threshold: 0.9
    enable_auto_rerender: true
  
  quality_gates:
    edge_weight: 0.4
    background_weight: 0.3
    color_weight: 0.2
    semantic_weight: 0.1
    pass_threshold: 0.85
```

## Troubleshooting

### Common Issues

1. **PaddleOCR Installation**: May require additional system dependencies
2. **Memory Usage**: Pre-analysis can be memory-intensive for large images
3. **Gemini API**: Requires valid API key and internet connection
4. **Schema Validation**: Ensure JSON files match V3.2 schema

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug output
python scripts/metrics_dashboard.py --results-dir results --output-dir debug_output
```

### Performance Optimization

- Use `enable_ocr=False` for faster pre-analysis
- Reduce `n_color_clusters` for simpler images
- Adjust thresholds based on quality requirements
- Use batch processing for multiple images

## Future Enhancements

### Planned Improvements

1. **Advanced OCR**: Better text detection and recognition
2. **Pattern Analysis**: More sophisticated texture analysis
3. **Quality Prediction**: ML-based quality prediction
4. **Automated Tuning**: Self-optimizing threshold adjustment
5. **Real-time Monitoring**: Live quality metrics dashboard

### Research Areas

1. **Perceptual Metrics**: Human perception-based quality assessment
2. **Domain Adaptation**: Garment-specific quality models
3. **Multi-modal Fusion**: Combining visual and semantic features
4. **Quality Prediction**: Predicting quality before generation

## Conclusion

Phase 2.1 significantly enhances the Photostudio.io pipeline with research-backed quality improvements. The implementation provides:

- **Enhanced Accuracy**: Better segmentation and analysis
- **Quality Assurance**: Comprehensive QA with semantic verification
- **Automation**: Reduced manual intervention through intelligent routing
- **Monitoring**: Detailed metrics and performance tracking
- **Scalability**: Robust architecture for production deployment

The phase maintains backward compatibility while providing significant improvements in quality, automation, and monitoring capabilities.
