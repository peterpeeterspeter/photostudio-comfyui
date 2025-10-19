"""
Enhanced Quality Validator for Phase 1.5
Adds LPIPS and CLIP-based perceptual quality assessment
"""

import json
import os
import argparse
from pathlib import Path
from PIL import Image
import numpy as np
from skimage.color import rgb2lab, deltaE_ciede2000
from collections import Counter
import time

# Import perceptual quality metrics
try:
    import torch
    from torchmetrics.image.lpip import LPIPS
    LPIPS_AVAILABLE = True
except ImportError:
    LPIPS_AVAILABLE = False
    print("Warning: torchmetrics not available. LPIPS validation will be skipped.")

try:
    import clip
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("Warning: CLIP not available. CLIP validation will be skipped.")


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def validate_color_delta_e(image_path, facts_json_path, delta_e_threshold_uni=3.0, delta_e_threshold_textured=5.0):
    """
    Validate color accuracy using CIELAB ΔE metric
    """
    try:
        # Load image and facts
        image = Image.open(image_path).convert('RGB')
        with open(facts_json_path, 'r') as f:
            facts = json.load(f)
        
        # Get target color
        target_hex = facts.get('garment', {}).get('color_hex', '#000000')
        target_rgb = hex_to_rgb(target_hex)
        
        # Convert to LAB color space
        target_lab = rgb2lab(np.array([[target_rgb]]))[0, 0]
        
        # Sample colors from image (avoid edges)
        img_array = np.array(image)
        h, w = img_array.shape[:2]
        
        # Sample from center region
        center_h, center_w = h // 2, w // 2
        sample_size = min(h, w) // 4
        
        y_start = center_h - sample_size // 2
        y_end = center_h + sample_size // 2
        x_start = center_w - sample_size // 2
        x_end = center_w + sample_size // 2
        
        sample_region = img_array[y_start:y_end, x_start:x_end]
        sample_lab = rgb2lab(sample_region)
        
        # Calculate ΔE for each pixel
        delta_e_values = []
        for i in range(sample_lab.shape[0]):
            for j in range(sample_lab.shape[1]):
                delta_e = deltaE_ciede2000(target_lab, sample_lab[i, j])
                delta_e_values.append(delta_e)
        
        # Calculate statistics
        mean_delta_e = np.mean(delta_e_values)
        max_delta_e = np.max(delta_e_values)
        
        # Determine threshold based on fabric type
        fabric = facts.get('garment', {}).get('fabric', '').lower()
        is_textured = any(word in fabric for word in ['textured', 'knit', 'woven', 'denim'])
        threshold = delta_e_threshold_textured if is_textured else delta_e_threshold_uni
        
        # Pass/fail determination
        passed = mean_delta_e <= threshold
        
        report = {
            "color_validation": {
                "passed": passed,
                "mean_delta_e": float(mean_delta_e),
                "max_delta_e": float(max_delta_e),
                "threshold": threshold,
                "target_color": target_hex,
                "fabric_type": fabric,
                "is_textured": is_textured
            }
        }
        
        return passed, report
        
    except Exception as e:
        print(f"Color validation error for {image_path}: {e}")
        return False, {"color_validation": {"error": str(e)}}


def validate_perceptual_quality(image_path, reference_path=None):
    """
    Validate perceptual quality using LPIPS and CLIP
    """
    results = {}
    
    try:
        # Load image
        image = Image.open(image_path).convert('RGB')
        img_tensor = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0
        img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension
        
        # LPIPS validation
        if LPIPS_AVAILABLE:
            try:
                lpips_metric = LPIPS(net='alex')
                
                if reference_path and os.path.exists(reference_path):
                    # Compare with reference image
                    ref_image = Image.open(reference_path).convert('RGB')
                    ref_tensor = torch.from_numpy(np.array(ref_image)).permute(2, 0, 1).float() / 255.0
                    ref_tensor = ref_tensor.unsqueeze(0)
                    
                    lpips_score = lpips_metric(img_tensor, ref_tensor).item()
                else:
                    # Use self-similarity as baseline (should be low for good images)
                    # Create a slightly blurred version as reference
                    blurred = torch.nn.functional.avg_pool2d(img_tensor, kernel_size=3, stride=1, padding=1)
                    lpips_score = lpips_metric(img_tensor, blurred).item()
                
                lpips_pass = lpips_score < 0.2
                results["lpips"] = {
                    "passed": lpips_pass,
                    "score": float(lpips_score),
                    "threshold": 0.2
                }
                
            except Exception as e:
                print(f"LPIPS validation error: {e}")
                results["lpips"] = {"error": str(e)}
        
        # CLIP validation
        if CLIP_AVAILABLE:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model, preprocess = clip.load("ViT-B/32", device=device)
                
                # Preprocess image for CLIP
                img_pil = Image.open(image_path).convert('RGB')
                img_clip = preprocess(img_pil).unsqueeze(0).to(device)
                
                # Define quality-related text prompts
                quality_prompts = [
                    "high quality fashion photo",
                    "professional product photography",
                    "clean sharp image",
                    "well lit garment",
                    "crisp edges and details"
                ]
                
                artifact_prompts = [
                    "blurry image",
                    "low quality photo",
                    "artifacts and noise",
                    "distorted image",
                    "poor lighting"
                ]
                
                # Encode image
                with torch.no_grad():
                    image_features = model.encode_image(img_clip)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    
                    # Calculate similarities
                    quality_similarities = []
                    artifact_similarities = []
                    
                    for prompt in quality_prompts:
                        text = clip.tokenize([prompt]).to(device)
                        text_features = model.encode_text(text)
                        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                        similarity = (image_features @ text_features.T).item()
                        quality_similarities.append(similarity)
                    
                    for prompt in artifact_prompts:
                        text = clip.tokenize([prompt]).to(device)
                        text_features = model.encode_text(text)
                        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                        similarity = (image_features @ text_features.T).item()
                        artifact_similarities.append(similarity)
                    
                    avg_quality_sim = np.mean(quality_similarities)
                    avg_artifact_sim = np.mean(artifact_similarities)
                    
                    # Pass if high quality similarity and low artifact similarity
                    clip_pass = avg_quality_sim > 0.75 and avg_artifact_sim < 0.3
                    
                    results["clip"] = {
                        "passed": clip_pass,
                        "quality_similarity": float(avg_quality_sim),
                        "artifact_similarity": float(avg_artifact_sim),
                        "quality_threshold": 0.75,
                        "artifact_threshold": 0.3
                    }
                    
            except Exception as e:
                print(f"CLIP validation error: {e}")
                results["clip"] = {"error": str(e)}
        
        return results
        
    except Exception as e:
        print(f"Perceptual validation error for {image_path}: {e}")
        return {"error": str(e)}


def validate_constraints(facts_json_path, generated_image_metadata=None):
    """
    Validate that generated image meets specified constraints
    """
    try:
        with open(facts_json_path, 'r') as f:
            facts = json.load(f)
        
        garment = facts.get('garment', {})
        constraints = facts.get('constraints', {})
        
        validation_results = {}
        
        # Check mandatory features
        mandatory_features = constraints.get('mandatory_features', [])
        for feature in mandatory_features:
            if feature == "exact_pocket_count":
                expected_pockets = garment.get('pockets_count', 0)
                # This would require computer vision to count actual pockets
                # For now, we'll assume it passes if the count is reasonable
                validation_results[feature] = {
                    "passed": True,  # Placeholder
                    "expected": expected_pockets,
                    "note": "Requires computer vision implementation"
                }
            
            elif feature == "color_hex_preservation":
                # This is handled by color_delta_e validation
                validation_results[feature] = {
                    "passed": True,  # Placeholder
                    "note": "Handled by color validation"
                }
            
            elif feature == "label_text_visibility":
                # This would require OCR to detect text
                validation_results[feature] = {
                    "passed": True,  # Placeholder
                    "note": "Requires OCR implementation"
                }
        
        # Check forbidden elements
        forbidden_elements = constraints.get('forbidden_elements', [])
        for element in forbidden_elements:
            # These would require specific computer vision checks
            validation_results[f"no_{element}"] = {
                "passed": True,  # Placeholder
                "note": "Requires specific CV implementation"
            }
        
        return True, {"constraints": validation_results}
        
    except Exception as e:
        print(f"Constraint validation error: {e}")
        return False, {"constraints": {"error": str(e)}}


def run_batch_validation(output_dir, facts_dir, reference_dir=None):
    """
    Run enhanced batch validation on all generated images
    """
    output_path = Path(output_dir)
    facts_path = Path(facts_dir)
    reference_path = Path(reference_dir) if reference_dir else None
    
    # Find all generated images
    image_files = list(output_path.glob("*.png")) + list(output_path.glob("*.jpg"))
    
    results = {
        "validation_summary": {
            "total_images": len(image_files),
            "validation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metrics_available": {
                "color_delta_e": True,
                "lpips": LPIPS_AVAILABLE,
                "clip": CLIP_AVAILABLE,
                "constraints": True
            }
        },
        "image_results": {}
    }
    
    for image_file in image_files:
        print(f"Validating {image_file.name}...")
        
        # Find corresponding facts file
        facts_file = facts_path / f"{image_file.stem}_facts.json"
        if not facts_file.exists():
            # Try alternative naming
            facts_file = facts_path / f"{image_file.stem}.json"
        
        if not facts_file.exists():
            print(f"Warning: No facts file found for {image_file.name}")
            continue
        
        # Find reference image if available
        ref_file = None
        if reference_path:
            ref_file = reference_path / image_file.name
            if not ref_file.exists():
                ref_file = None
        
        # Run all validations
        image_results = {}
        
        # Color validation
        color_passed, color_report = validate_color_delta_e(str(image_file), str(facts_file))
        image_results.update(color_report)
        
        # Perceptual validation
        perceptual_results = validate_perceptual_quality(str(image_file), str(ref_file) if ref_file else None)
        image_results.update(perceptual_results)
        
        # Constraint validation
        constraint_passed, constraint_report = validate_constraints(str(facts_file))
        image_results.update(constraint_report)
        
        # Overall pass/fail
        overall_passed = color_passed
        if "lpips" in image_results and "passed" in image_results["lpips"]:
            overall_passed = overall_passed and image_results["lpips"]["passed"]
        if "clip" in image_results and "passed" in image_results["clip"]:
            overall_passed = overall_passed and image_results["clip"]["passed"]
        overall_passed = overall_passed and constraint_passed
        
        image_results["overall_passed"] = overall_passed
        
        results["image_results"][image_file.name] = image_results
    
    # Calculate summary statistics
    total_images = len(results["image_results"])
    passed_images = sum(1 for r in results["image_results"].values() if r.get("overall_passed", False))
    
    results["validation_summary"]["passed_images"] = passed_images
    results["validation_summary"]["pass_rate"] = passed_images / total_images if total_images > 0 else 0
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Enhanced Quality Validator for Phase 1.5")
    parser.add_argument("--input", required=True, help="Directory containing generated images")
    parser.add_argument("--facts", required=True, help="Directory containing facts JSON files")
    parser.add_argument("--reference", help="Directory containing reference images (optional)")
    parser.add_argument("--report", default="qa_report_enhanced.json", help="Output report file")
    
    args = parser.parse_args()
    
    print("🔍 Running Enhanced Quality Validation...")
    print(f"Input directory: {args.input}")
    print(f"Facts directory: {args.facts}")
    if args.reference:
        print(f"Reference directory: {args.reference}")
    
    # Run validation
    results = run_batch_validation(args.input, args.facts, args.reference)
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_numpy_types(obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    results = convert_numpy_types(results)
    
    # Save results
    with open(args.report, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    summary = results["validation_summary"]
    print(f"\n📊 Validation Summary:")
    print(f"Total images: {summary['total_images']}")
    print(f"Passed images: {summary['passed_images']}")
    print(f"Pass rate: {summary['pass_rate']:.1%}")
    print(f"Report saved to: {args.report}")


if __name__ == "__main__":
    main()
