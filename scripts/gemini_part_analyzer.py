#!/usr/bin/env python3
"""
Gemini Part Analyzer for Photostudio.io Phase 2
Analyzes garment parts using Gemini Flash Lite 2.5
"""

import os
import json
import argparse
from pathlib import Path
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

genai.configure(api_key=api_key)

PART_PROMPT_TEMPLATE = """
Analyze this {part_name} from a {garment_category}.

Context:
- Dominant colors detected: {dominant_colors}
- Pattern complexity: {pattern_complexity}
- Text present: {text_detected}
- Exposure level: {exposure}

Identify (JSON only):
{{
  "color_hex": "#RRGGBB",
  "texture": "smooth|ribbed|woven|knit",
  "pattern": "solid|striped|printed|textured",
  "condition": "clean|wrinkled|stained",
  "seam_quality": 0.0-1.0,
  "sharpness_needed": 0.0-1.0,
  "transparency": 0.0-1.0,
  "risk_score": 0.0-1.0
}}
"""

ENHANCED_PART_PROMPT_TEMPLATE = """
Analyze this {part_name} from a {garment_category}.

Pre-analysis Context:
- Dominant colors detected: {dominant_colors}
- Pattern complexity: {pattern_complexity}
- Text present: {text_detected}
- Exposure level: {exposure}
- Contrast level: {contrast}

Use this context to improve your analysis accuracy. Consider how the pre-analysis features
relate to the specific part you're analyzing.

Identify (JSON only):
{{
  "color_hex": "#RRGGBB",
  "texture": "smooth|ribbed|woven|knit",
  "pattern": "solid|striped|printed|textured",
  "condition": "clean|wrinkled|stained",
  "seam_quality": 0.0-1.0,
  "sharpness_needed": 0.0-1.0,
  "transparency": 0.0-1.0,
  "risk_score": 0.0-1.0,
  "context_alignment": 0.0-1.0
}}
"""


def analyze_garment_part(image_path: str, part_name: str, garment_category: str, 
                        pre_features: dict = None) -> dict:
    """
    Analyze single garment part using Gemini Flash Lite 2.5
    Enhanced with pre-analysis context for improved accuracy
    
    Args:
        image_path: Path to the part image
        part_name: Name of the garment part
        garment_category: Category of the garment
        pre_features: Pre-analysis features dict with dominant_colors, pattern_complexity, etc.
    
    Returns:
        dict: Structured JSON with per-part attributes
    """
    if not os.environ.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not found, using fallback analysis")
        return _fallback_part_analysis(part_name, garment_category, pre_features)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        image = Image.open(image_path)
        
        # Use enhanced prompt if pre-analysis features are available
        if pre_features:
            prompt = ENHANCED_PART_PROMPT_TEMPLATE.format(
                part_name=part_name,
                garment_category=garment_category,
                dominant_colors=", ".join(pre_features.get("dominant_colors", ["#000000"])),
                pattern_complexity=pre_features.get("pattern_complexity", "medium"),
                text_detected=pre_features.get("text_detected", False),
                exposure=pre_features.get("exposure", 0.5),
                contrast=pre_features.get("contrast", 0.5)
            )
            print(f"Enhanced Gemini analysis for {part_name} with pre-analysis context")
        else:
            # Fallback to basic prompt
            prompt = PART_PROMPT_TEMPLATE.format(
                part_name=part_name,
                garment_category=garment_category,
                dominant_colors="#000000",
                pattern_complexity="medium",
                text_detected=False,
                exposure=0.5
            )
            print(f"Basic Gemini analysis for {part_name} (no pre-analysis context)")
        
        response = model.generate_content([prompt, image])
        
        # Clean the response text (remove markdown code blocks)
        clean_text = response.text.strip()
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:]  # Remove ```json
        if clean_text.endswith('```'):
            clean_text = clean_text[:-3]  # Remove ```
        clean_text = clean_text.strip()
        
        part_data = json.loads(clean_text)
        part_data["part_name"] = part_name
        part_data["analyzed"] = True
        part_data["analysis_method"] = "gemini_enhanced" if pre_features else "gemini_basic"
        
        # Add pre-analysis context info if available
        if pre_features:
            part_data["pre_analysis_used"] = True
            part_data["context_features"] = {
                "dominant_colors": pre_features.get("dominant_colors", []),
                "pattern_complexity": pre_features.get("pattern_complexity", "medium"),
                "text_detected": pre_features.get("text_detected", False),
                "exposure": pre_features.get("exposure", 0.5),
                "contrast": pre_features.get("contrast", 0.5)
            }
        else:
            part_data["pre_analysis_used"] = False
        
        print(f"✅ Gemini analysis completed for {part_name}")
        return part_data
        
    except Exception as e:
        print(f"❌ Gemini analysis failed for {part_name}: {e}")
        return _fallback_part_analysis(part_name, garment_category, pre_features)


def _fallback_part_analysis(part_name: str, garment_category: str, pre_features: dict = None) -> dict:
    """Fallback analysis when Gemini API is not available"""
    # Provide reasonable defaults based on part type
    defaults = {
        "collar": {
            "color_hex": "#FFFFFF",
            "texture": "smooth",
            "pattern": "solid",
            "condition": "clean",
            "seam_quality": 0.8,
            "sharpness_needed": 0.9,
            "transparency": 0.0
        },
        "sleeve": {
            "color_hex": "#FFFFFF", 
            "texture": "woven",
            "pattern": "solid",
            "condition": "clean",
            "seam_quality": 0.7,
            "sharpness_needed": 0.8,
            "transparency": 0.0
        },
        "body": {
            "color_hex": "#FFFFFF",
            "texture": "woven", 
            "pattern": "solid",
            "condition": "clean",
            "seam_quality": 0.8,
            "sharpness_needed": 0.7,
            "transparency": 0.0
        },
        "pocket": {
            "color_hex": "#FFFFFF",
            "texture": "woven",
            "pattern": "solid", 
            "condition": "clean",
            "seam_quality": 0.9,
            "sharpness_needed": 0.8,
            "transparency": 0.0
        }
    }
    
    # Find best match for part name
    part_key = "body"  # default
    for key in defaults:
        if key in part_name.lower():
            part_key = key
            break
    
    fallback_data = defaults[part_key].copy()
    fallback_data["part_name"] = part_name
    fallback_data["analyzed"] = False
    fallback_data["analysis_method"] = "fallback"
    fallback_data["error"] = "Gemini API not available"
    
    # Enhance fallback with pre-analysis context if available
    if pre_features:
        fallback_data["pre_analysis_used"] = True
        fallback_data["analysis_method"] = "fallback_enhanced"
        
        # Use dominant color from pre-analysis if available
        dominant_colors = pre_features.get("dominant_colors", [])
        if dominant_colors:
            fallback_data["color_hex"] = dominant_colors[0]  # Use first dominant color
        
        # Adjust based on pattern complexity
        pattern_complexity = pre_features.get("pattern_complexity", "medium")
        if pattern_complexity == "high":
            fallback_data["pattern"] = "printed"
            fallback_data["risk_score"] = 0.7  # Higher risk for complex patterns
        elif pattern_complexity == "low":
            fallback_data["pattern"] = "solid"
            fallback_data["risk_score"] = 0.3  # Lower risk for simple patterns
        
        # Adjust based on exposure
        exposure = pre_features.get("exposure", 0.5)
        if exposure < 0.3:  # Low exposure
            fallback_data["condition"] = "dark"
            fallback_data["sharpness_needed"] = 0.9  # Need more sharpness for dark areas
        elif exposure > 0.7:  # High exposure
            fallback_data["condition"] = "bright"
            fallback_data["transparency"] = 0.2  # Might be overexposed
        
        fallback_data["context_features"] = {
            "dominant_colors": dominant_colors,
            "pattern_complexity": pattern_complexity,
            "text_detected": pre_features.get("text_detected", False),
            "exposure": exposure,
            "contrast": pre_features.get("contrast", 0.5)
        }
    else:
        fallback_data["pre_analysis_used"] = False
    
    return fallback_data


def batch_analyze_garment(parts_json_path: str, crops_dir: str, pre_features: dict = None) -> dict:
    """
    Analyze all parts from segmentation output
    Enhanced with pre-analysis context for improved accuracy
    
    Args:
        parts_json_path: Path to parts JSON from segmentation
        crops_dir: Directory containing cropped part images
        pre_features: Pre-analysis features dict with dominant_colors, pattern_complexity, etc.
    
    Returns:
        dict: Complete Facts V3.1 JSON with enhanced analysis
    """
    with open(parts_json_path) as f:
        parts = json.load(f)
    
    analyzed_parts = []
    garment_category = parts.get("garment_category", "dress_shirt")
    
    for part in parts["parts"]:
        crop_path = f"{crops_dir}/{parts['sku']}_{part['part_name']}.png"
        
        if os.path.exists(crop_path):
            analysis = analyze_garment_part(crop_path, part['part_name'], garment_category, pre_features)
            analyzed_parts.append(analysis)
        else:
            print(f"Warning: Crop file not found: {crop_path}")
            # Use fallback analysis
            analysis = _fallback_part_analysis(part['part_name'], garment_category, pre_features)
            analyzed_parts.append(analysis)
    
    # Aggregate into Facts V3.1 schema (enhanced with pre-analysis)
    facts_v3_1 = {
        "schema_version": "3.1",
        "analysis_mode": "full",
        "garment": {
            "category": garment_category,
            "parts": analyzed_parts,
            # Aggregate color from parts
            "color_hex": _aggregate_color(analyzed_parts),
            "color_name": _hex_to_color_name(_aggregate_color(analyzed_parts)),
            "pattern": _aggregate_pattern(analyzed_parts),
            "transparency_level": _aggregate_transparency(analyzed_parts),
            "complexity_score": _calculate_complexity_score(analyzed_parts)
        },
        "photography": {
            "bg": "pure_white",
            "lighting": "soft_even_high_key", 
            "frame": "4:5",
            "coverage_pct": 85
        },
        "routing": {
            "suggested_model": "sdxl",
            "use_ip_adapter": _should_use_ip_adapter(analyzed_parts),
            "use_controlnet_inpaint": True
        },
        "risk_score": _calculate_risk_score(analyzed_parts)
    }
    
    # Add pre-analysis context if available
    if pre_features:
        facts_v3_1["pre_analysis"] = {
            "dominant_colors": pre_features.get("dominant_colors", []),
            "pattern_complexity": pre_features.get("pattern_complexity", "medium"),
            "text_detected": pre_features.get("text_detected", False),
            "text_boxes": pre_features.get("text_boxes", []),
            "exposure": pre_features.get("exposure", 0.5),
            "contrast": pre_features.get("contrast", 0.5)
        }
        facts_v3_1["analysis_enhanced"] = True
        print("✅ Facts V3.1 enhanced with pre-analysis context")
    else:
        facts_v3_1["analysis_enhanced"] = False
    
    return facts_v3_1


def _aggregate_color(parts):
    """Aggregate dominant color from all parts"""
    colors = [part.get("color_hex", "#FFFFFF") for part in parts if part.get("color_hex")]
    if not colors:
        return "#FFFFFF"
    
    # Simple aggregation - return most common color
    from collections import Counter
    color_counts = Counter(colors)
    return color_counts.most_common(1)[0][0]


def _hex_to_color_name(hex_color):
    """Convert hex color to color name"""
    color_map = {
        "#FFFFFF": "white",
        "#000000": "black", 
        "#FF0000": "red",
        "#00FF00": "green",
        "#0000FF": "blue",
        "#FFFF00": "yellow",
        "#FF00FF": "magenta",
        "#00FFFF": "cyan",
        "#FFA500": "orange",
        "#800080": "purple",
        "#1a237e": "navy blue"
    }
    return color_map.get(hex_color.upper(), "unknown")


def _aggregate_pattern(parts):
    """Aggregate pattern from all parts"""
    patterns = [part.get("pattern", "solid") for part in parts if part.get("pattern")]
    if not patterns:
        return "solid"
    
    # Return most complex pattern
    pattern_priority = ["printed", "striped", "textured", "solid"]
    for pattern in pattern_priority:
        if pattern in patterns:
            return pattern
    return "solid"


def _aggregate_transparency(parts):
    """Aggregate transparency level from all parts"""
    transparencies = [part.get("transparency", 0.0) for part in parts if part.get("transparency") is not None]
    if not transparencies:
        return 0.0
    
    return max(transparencies)  # Use highest transparency level


def _calculate_complexity_score(parts):
    """Calculate complexity score based on parts analysis"""
    if not parts:
        return 0.0
    
    complexity_factors = []
    
    for part in parts:
        # Pattern complexity
        pattern = part.get("pattern", "solid")
        if pattern == "printed":
            complexity_factors.append(0.8)
        elif pattern == "striped":
            complexity_factors.append(0.6)
        elif pattern == "textured":
            complexity_factors.append(0.4)
        else:
            complexity_factors.append(0.2)
        
        # Seam quality affects complexity
        seam_quality = part.get("seam_quality", 0.5)
        complexity_factors.append(1.0 - seam_quality)  # Lower quality = higher complexity
    
    return min(sum(complexity_factors) / len(complexity_factors), 1.0)


def _should_use_ip_adapter(parts):
    """Determine if IP-Adapter should be used based on parts analysis"""
    for part in parts:
        pattern = part.get("pattern", "solid")
        if pattern != "solid":
            return True
    return False


def _calculate_risk_score(parts):
    """Calculate risk score based on parts analysis"""
    if not parts:
        return 0.5
    
    risk_factors = []
    
    for part in parts:
        # Pattern complexity increases risk
        pattern = part.get("pattern", "solid")
        if pattern == "printed":
            risk_factors.append(0.8)
        elif pattern == "striped":
            risk_factors.append(0.6)
        elif pattern == "textured":
            risk_factors.append(0.4)
        else:
            risk_factors.append(0.2)
        
        # Transparency increases risk
        transparency = part.get("transparency", 0.0)
        risk_factors.append(transparency)
        
        # Lower seam quality increases risk
        seam_quality = part.get("seam_quality", 0.5)
        risk_factors.append(1.0 - seam_quality)
    
    return min(sum(risk_factors) / len(risk_factors), 1.0)


def main():
    """Command line interface for Gemini part analyzer"""
    parser = argparse.ArgumentParser(description="Analyze garment parts using Gemini Flash Lite")
    parser.add_argument("--parts-json", required=True, help="Path to parts JSON file")
    parser.add_argument("--crops-dir", required=True, help="Directory containing part crops")
    parser.add_argument("--output", required=True, help="Output Facts V3.1 JSON file")
    
    args = parser.parse_args()
    
    print(f"🔍 Analyzing garment parts from {args.parts_json}")
    print(f"📁 Crops directory: {args.crops_dir}")
    
    try:
        facts_v3_1 = batch_analyze_garment(args.parts_json, args.crops_dir)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(facts_v3_1, f, indent=2)
        
        print(f"✅ Analysis complete! Results saved to {args.output}")
        print(f"📊 Analyzed {len(facts_v3_1['garment']['parts'])} parts")
        print(f"🎨 Dominant color: {facts_v3_1['garment']['color_hex']} ({facts_v3_1['garment']['color_name']})")
        print(f"📐 Pattern: {facts_v3_1['garment']['pattern']}")
        print(f"⚠️  Risk score: {facts_v3_1['risk_score']:.2f}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
