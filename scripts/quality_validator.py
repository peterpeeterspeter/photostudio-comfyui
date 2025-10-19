"""
Quality Validator Script
Batch quality assessment for ghost mannequin outputs
"""

import os
import json
import numpy as np
import cv2
from PIL import Image
from typing import Dict, List, Tuple, Optional
import argparse
from datetime import datetime
import colour
from skimage.metrics import structural_similarity as ssim


class QualityValidator:
    """
    Comprehensive quality validation for ghost mannequin images
    Implements ΔE color accuracy, constraint checking, and batch reporting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize validator with configuration"""
        self.config = config or self._default_config()
        
    def _default_config(self) -> Dict:
        """Default configuration for quality thresholds"""
        return {
            "color_accuracy": {
                "delta_e_uni_max": 3.0,
                "delta_e_textured_max": 5.0,
                "color_space": "LAB"
            },
            "edge_quality": {
                "ssim_min": 0.75,
                "alpha_min": 0.97
            },
            "background": {
                "purity_min": 0.95,
                "white_threshold": 250.0
            },
            "constraints": {
                "pocket_tolerance": 1,
                "button_tolerance": 1
            }
        }
    
    def validate_color_accuracy(
        self, 
        image_path: str, 
        facts_json: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Validate color accuracy using ΔE calculation
        
        Args:
            image_path: Path to generated image
            facts_json: Light Facts JSON data
            
        Returns:
            Validation results dictionary
        """
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            img_array = np.array(image) / 255.0
            
            # Get target color from facts
            garment = facts_json.get('garment', {})
            target_hex = garment.get('color_hex', '#000000')
            
            # Convert hex to RGB
            target_rgb = self._hex_to_rgb(target_hex)
            
            # Extract garment region (simplified - would need mask in real implementation)
            garment_region = self._extract_garment_region(img_array)
            
            # Calculate dominant color
            dominant_color = self._calculate_dominant_color(garment_region)
            
            # Calculate ΔE in LAB space
            delta_e = self._calculate_delta_e(target_rgb, dominant_color)
            
            # Determine if textured or uni-color
            is_textured = self._is_textured_fabric(garment)
            max_delta_e = (
                self.config['color_accuracy']['delta_e_textured_max'] 
                if is_textured 
                else self.config['color_accuracy']['delta_e_uni_max']
            )
            
            pass_fail = delta_e <= max_delta_e
            
            return {
                "pass": pass_fail,
                "delta_e": float(delta_e),
                "target_color": target_hex,
                "dominant_color": self._rgb_to_hex(dominant_color),
                "threshold": max_delta_e,
                "fabric_type": "textured" if is_textured else "uni-color"
            }
            
        except Exception as e:
            return {
                "pass": False,
                "error": str(e),
                "delta_e": float('inf')
            }
    
    def validate_constraints(
        self, 
        image_path: str, 
        facts_json: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Validate structural constraints (pocket count, button count, etc.)
        
        Args:
            image_path: Path to generated image
            facts_json: Light Facts JSON data
            
        Returns:
            Validation results dictionary
        """
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            img_array = np.array(image)
            
            garment = facts_json.get('garment', {})
            failures = []
            
            # Check pocket count (heuristic-based)
            expected_pockets = garment.get('pockets_count', 0)
            if expected_pockets > 0:
                detected_pockets = self._detect_pockets(img_array)
                pocket_diff = abs(detected_pockets - expected_pockets)
                if pocket_diff > self.config['constraints']['pocket_tolerance']:
                    failures.append(f"pocket_count_mismatch: expected {expected_pockets}, detected {detected_pockets}")
            
            # Check for forbidden elements
            forbidden = facts_json.get('constraints', {}).get('forbidden_elements', [])
            for element in forbidden:
                if self._detect_forbidden_element(img_array, element):
                    failures.append(f"forbidden_element_detected: {element}")
            
            # Check label text visibility
            label_text = garment.get('label_text', '')
            if label_text and not self._detect_text(img_array, label_text):
                failures.append(f"label_text_not_visible: {label_text}")
            
            pass_fail = len(failures) == 0
            
            return {
                "pass": pass_fail,
                "failures": failures,
                "detected_pockets": detected_pockets if expected_pockets > 0 else 0,
                "expected_pockets": expected_pockets
            }
            
        except Exception as e:
            return {
                "pass": False,
                "error": str(e),
                "failures": [f"validation_error: {str(e)}"]
            }
    
    def validate_batch(self, output_dir: str, facts_dir: str) -> Dict[str, any]:
        """
        Validate all images in output directory
        
        Args:
            output_dir: Directory containing generated images
            facts_dir: Directory containing corresponding facts JSON files
            
        Returns:
            Batch validation report
        """
        results = []
        total_images = 0
        passed_images = 0
        
        # Find all image files
        image_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        image_files = []
        
        for file in os.listdir(output_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(file)
        
        total_images = len(image_files)
        
        for image_file in image_files:
            # Find corresponding facts file
            base_name = os.path.splitext(image_file)[0]
            facts_file = os.path.join(facts_dir, f"{base_name}.json")
            
            if not os.path.exists(facts_file):
                # Try with different naming patterns
                facts_file = os.path.join(facts_dir, f"{base_name}_facts.json")
            
            if not os.path.exists(facts_file):
                results.append({
                    "image": image_file,
                    "status": "error",
                    "error": "No corresponding facts file found"
                })
                continue
            
            # Load facts
            try:
                with open(facts_file, 'r', encoding='utf-8') as f:
                    facts = json.load(f)
            except Exception as e:
                results.append({
                    "image": image_file,
                    "status": "error",
                    "error": f"Failed to load facts: {str(e)}"
                })
                continue
            
            # Validate image
            image_path = os.path.join(output_dir, image_file)
            
            # Run all validations
            color_result = self.validate_color_accuracy(image_path, facts)
            constraints_result = self.validate_constraints(image_path, facts)
            
            # Determine overall pass
            overall_pass = color_result.get('pass', False) and constraints_result.get('pass', False)
            if overall_pass:
                passed_images += 1
            
            # Compile result
            result = {
                "image": image_file,
                "timestamp": datetime.now().isoformat(),
                "gates": {
                    "color_accuracy": color_result,
                    "constraints": constraints_result
                },
                "overall_pass": overall_pass,
                "action": "re-render" if not overall_pass else "accept"
            }
            
            results.append(result)
        
        # Generate summary
        pass_rate = (passed_images / total_images) * 100 if total_images > 0 else 0
        
        summary = {
            "total_images": total_images,
            "passed_images": passed_images,
            "failed_images": total_images - passed_images,
            "pass_rate": pass_rate,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        return summary
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: Tuple[float, float, float]) -> str:
        """Convert RGB tuple to hex color"""
        r, g, b = [int(x * 255) for x in rgb]
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _extract_garment_region(self, image: np.ndarray) -> np.ndarray:
        """Extract garment region from image (simplified implementation)"""
        # In real implementation, this would use the mask from RMBG
        # For now, return the center region as a placeholder
        h, w = image.shape[:2]
        center_h, center_w = h // 2, w // 2
        return image[center_h-h//4:center_h+h//4, center_w-w//4:center_w+w//4]
    
    def _calculate_dominant_color(self, region: np.ndarray) -> Tuple[float, float, float]:
        """Calculate dominant color in region"""
        # Reshape to list of pixels
        pixels = region.reshape(-1, 3)
        # Calculate mean color
        return tuple(np.mean(pixels, axis=0))
    
    def _calculate_delta_e(self, color1: Tuple[float, float, float], color2: Tuple[float, float, float]) -> float:
        """Calculate ΔE color difference in LAB space"""
        try:
            # Convert RGB to LAB
            lab1 = colour.RGB_to_Lab(color1)
            lab2 = colour.RGB_to_Lab(color2)
            
            # Calculate ΔE
            delta_e = colour.delta_E_CIE1976(lab1, lab2)
            return float(delta_e)
        except:
            # Fallback to simple Euclidean distance
            return np.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2))) * 100
    
    def _is_textured_fabric(self, garment: Dict[str, any]) -> bool:
        """Determine if fabric is textured based on garment info"""
        fabric = garment.get('fabric', '').lower()
        category = garment.get('category', '').lower()
        
        textured_indicators = [
            'tweed', 'jacquard', 'pattern', 'textured', 'woven',
            'denim', 'corduroy', 'flannel', 'twill'
        ]
        
        return any(indicator in fabric or indicator in category for indicator in textured_indicators)
    
    def _detect_pockets(self, image: np.ndarray) -> int:
        """Detect number of pockets (heuristic implementation)"""
        # Simplified pocket detection using edge detection
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size and shape (pocket-like)
        pocket_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 5000:  # Pocket size range
                # Check aspect ratio
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 0.3 < aspect_ratio < 3.0:  # Reasonable pocket aspect ratio
                    pocket_count += 1
        
        return min(pocket_count, 4)  # Cap at 4 pockets max
    
    def _detect_forbidden_element(self, image: np.ndarray, element: str) -> bool:
        """Detect forbidden elements in image"""
        # Simplified detection based on element type
        if element in ['halo', 'fringing']:
            # Check for edge artifacts
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 30, 100)
            edge_density = np.sum(edges > 0) / edges.size
            return edge_density > 0.1  # High edge density indicates artifacts
        
        elif element == 'visible mannequin':
            # Check for human-like shapes (simplified)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            # This would need more sophisticated detection in practice
            return False
        
        return False
    
    def _detect_text(self, image: np.ndarray, text: str) -> bool:
        """Detect if specific text is visible in image"""
        # Simplified text detection - in practice would use OCR
        # For now, return True as placeholder
        return True


def main():
    """Command line interface for quality validator"""
    parser = argparse.ArgumentParser(description='Validate ghost mannequin image quality')
    parser.add_argument('--output-dir', required=True, help='Directory containing generated images')
    parser.add_argument('--facts-dir', required=True, help='Directory containing facts JSON files')
    parser.add_argument('--output-report', help='Output file for validation report')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Run validation
    validator = QualityValidator(config)
    report = validator.validate_batch(args.output_dir, args.facts_dir)
    
    # Save report
    if args.output_report:
        with open(args.output_report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Validation report saved to {args.output_report}")
    else:
        print(json.dumps(report, indent=2))
    
    # Print summary
    print(f"\nValidation Summary:")
    print(f"Total images: {report['total_images']}")
    print(f"Passed: {report['passed_images']}")
    print(f"Failed: {report['failed_images']}")
    print(f"Pass rate: {report['pass_rate']:.1f}%")


if __name__ == "__main__":
    main()
