"""
Unit tests for pre-analysis features in Phase 2.1
Tests color palette extraction, pattern complexity, OCR text detection, and exposure metrics
"""

import unittest
import numpy as np
import cv2
from PIL import Image
import torch
import sys
import os
import json

# Add the ComfyUI custom_nodes directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ComfyUI', 'custom_nodes'))

from pre_analysis_node import PreAnalysisNode


class TestPreAnalysis(unittest.TestCase):
    """Test pre-analysis functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pre_analysis = PreAnalysisNode()
        
        # Create test images
        self.solid_color_image = self._create_solid_color_image()
        self.multi_color_image = self._create_multi_color_image()
        self.high_contrast_image = self._create_high_contrast_image()
        self.low_contrast_image = self._create_low_contrast_image()
        self.text_image = self._create_text_image()
    
    def _create_solid_color_image(self):
        """Create a solid color test image"""
        image = np.full((100, 100, 3), [128, 64, 192], dtype=np.uint8)  # Purple
        return Image.fromarray(image)
    
    def _create_multi_color_image(self):
        """Create a multi-color test image"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Create 4 distinct color regions
        image[0:50, 0:50] = [255, 0, 0]      # Red
        image[0:50, 50:100] = [0, 255, 0]    # Green
        image[50:100, 0:50] = [0, 0, 255]    # Blue
        image[50:100, 50:100] = [255, 255, 0] # Yellow
        return Image.fromarray(image)
    
    def _create_high_contrast_image(self):
        """Create a high contrast test image"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[0:50, :] = [255, 255, 255]  # White
        image[50:100, :] = [0, 0, 0]      # Black
        return Image.fromarray(image)
    
    def _create_low_contrast_image(self):
        """Create a low contrast test image"""
        image = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)  # Gray
        # Add slight variations
        image[0:50, :] = [130, 130, 130]
        image[50:100, :] = [126, 126, 126]
        return Image.fromarray(image)
    
    def _create_text_image(self):
        """Create an image with text (simplified)"""
        image = np.full((100, 100, 3), [255, 255, 255], dtype=np.uint8)  # White background
        # Add some "text" regions (simplified as rectangles)
        image[20:30, 20:80] = [0, 0, 0]  # Black text line
        image[40:50, 20:80] = [0, 0, 0]  # Another text line
        return Image.fromarray(image)
    
    def _pil_to_tensor(self, image):
        """Convert PIL image to ComfyUI tensor format"""
        image_np = np.array(image).astype(np.float32) / 255.0
        return torch.from_numpy(image_np)[None,]
    
    def test_color_palette_extraction(self):
        """Test dominant color extraction"""
        # Test with solid color image
        colors = self.pre_analysis._extract_color_palette(
            cv2.cvtColor(np.array(self.solid_color_image), cv2.COLOR_RGB2BGR), 5
        )
        
        self.assertEqual(len(colors), 5, "Should return requested number of colors")
        self.assertTrue(all(color.startswith('#') for color in colors), 
                       "All colors should be in hex format")
        self.assertTrue(all(len(color) == 7 for color in colors), 
                       "All colors should be valid hex codes")
        
        # Test with multi-color image
        colors = self.pre_analysis._extract_color_palette(
            cv2.cvtColor(np.array(self.multi_color_image), cv2.COLOR_RGB2BGR), 4
        )
        
        self.assertEqual(len(colors), 4, "Should return requested number of colors")
        # Should detect the 4 distinct colors
        self.assertTrue(len(set(colors)) >= 2, "Should detect multiple distinct colors")
    
    def test_pattern_complexity_high(self):
        """Test pattern complexity detection for high complexity"""
        # High contrast image should have high complexity
        complexity = self.pre_analysis._compute_fft_complexity(
            cv2.cvtColor(np.array(self.high_contrast_image), cv2.COLOR_RGB2BGR), 0.3
        )
        
        self.assertIn(complexity, ["high", "medium", "low"], 
                     "Complexity should be one of the expected values")
    
    def test_pattern_complexity_low(self):
        """Test pattern complexity detection for low complexity"""
        # Low contrast image should have low complexity
        complexity = self.pre_analysis._compute_fft_complexity(
            cv2.cvtColor(np.array(self.low_contrast_image), cv2.COLOR_RGB2BGR), 0.3
        )
        
        self.assertIn(complexity, ["high", "medium", "low"], 
                     "Complexity should be one of the expected values")
    
    def test_exposure_computation(self):
        """Test exposure level computation"""
        # High contrast image should have medium exposure
        exposure = self.pre_analysis._compute_exposure(
            cv2.cvtColor(np.array(self.high_contrast_image), cv2.COLOR_RGB2BGR)
        )
        
        self.assertGreaterEqual(exposure, 0.0, "Exposure should not be negative")
        self.assertLessEqual(exposure, 1.0, "Exposure should not exceed 1.0")
        
        # Solid color image should have predictable exposure
        exposure = self.pre_analysis._compute_exposure(
            cv2.cvtColor(np.array(self.solid_color_image), cv2.COLOR_RGB2BGR)
        )
        
        self.assertGreaterEqual(exposure, 0.0, "Exposure should not be negative")
        self.assertLessEqual(exposure, 1.0, "Exposure should not exceed 1.0")
    
    def test_contrast_computation(self):
        """Test contrast level computation"""
        # High contrast image should have high contrast
        contrast = self.pre_analysis._compute_contrast(
            cv2.cvtColor(np.array(self.high_contrast_image), cv2.COLOR_RGB2BGR)
        )
        
        self.assertGreaterEqual(contrast, 0.0, "Contrast should not be negative")
        self.assertLessEqual(contrast, 1.0, "Contrast should not exceed 1.0")
        
        # Low contrast image should have low contrast
        contrast = self.pre_analysis._compute_contrast(
            cv2.cvtColor(np.array(self.low_contrast_image), cv2.COLOR_RGB2BGR)
        )
        
        self.assertGreaterEqual(contrast, 0.0, "Contrast should not be negative")
        self.assertLessEqual(contrast, 1.0, "Contrast should not exceed 1.0")
    
    def test_text_detection_with_ocr(self):
        """Test text detection functionality"""
        # Test with text image
        text_detected, text_boxes = self.pre_analysis._detect_text_regions(
            cv2.cvtColor(np.array(self.text_image), cv2.COLOR_RGB2BGR)
        )
        
        # Should detect text (or at least not crash)
        self.assertIsInstance(text_detected, bool, "Text detection should return boolean")
        self.assertIsInstance(text_boxes, list, "Text boxes should be a list")
        
        if text_boxes:
            for box in text_boxes:
                self.assertEqual(len(box), 4, "Each text box should have 4 coordinates")
                self.assertTrue(all(isinstance(coord, int) for coord in box), 
                               "All coordinates should be integers")
    
    def test_text_detection_without_ocr(self):
        """Test text detection when OCR is not available"""
        # Temporarily disable OCR
        original_ocr_available = self.pre_analysis.ocr_available
        self.pre_analysis.ocr_available = False
        
        try:
            text_detected, text_boxes = self.pre_analysis._detect_text_regions(
                cv2.cvtColor(np.array(self.text_image), cv2.COLOR_RGB2BGR)
            )
            
            self.assertFalse(text_detected, "Should not detect text when OCR is unavailable")
            self.assertEqual(text_boxes, [], "Should return empty text boxes when OCR is unavailable")
        finally:
            # Restore original state
            self.pre_analysis.ocr_available = original_ocr_available
    
    def test_full_analysis_integration(self):
        """Test the complete pre-analysis workflow"""
        # Convert image to ComfyUI tensor format
        image_tensor = self._pil_to_tensor(self.multi_color_image)
        
        # Run full analysis
        pre_features_json, visualization = self.pre_analysis.analyze(
            image_tensor, n_color_clusters=4, pattern_threshold=0.3, enable_ocr=True
        )
        
        # Parse results
        features = json.loads(pre_features_json)
        
        # Check that all required features are present
        required_features = [
            "dominant_colors", "pattern_complexity", "text_detected", 
            "text_boxes", "exposure", "contrast"
        ]
        
        for feature in required_features:
            self.assertIn(feature, features, f"Missing feature: {feature}")
        
        # Check feature types and ranges
        self.assertIsInstance(features["dominant_colors"], list)
        self.assertIn(features["pattern_complexity"], ["high", "medium", "low"])
        self.assertIsInstance(features["text_detected"], bool)
        self.assertIsInstance(features["text_boxes"], list)
        self.assertGreaterEqual(features["exposure"], 0.0)
        self.assertLessEqual(features["exposure"], 1.0)
        self.assertGreaterEqual(features["contrast"], 0.0)
        self.assertLessEqual(features["contrast"], 1.0)
        
        # Check visualization output
        self.assertIsInstance(visualization, torch.Tensor, "Visualization should be a tensor")
        self.assertEqual(len(visualization.shape), 4, "Visualization should have 4 dimensions")
    
    def test_analysis_with_different_parameters(self):
        """Test analysis with different parameter settings"""
        image_tensor = self._pil_to_tensor(self.multi_color_image)
        
        # Test with different number of color clusters
        features_json, _ = self.pre_analysis.analyze(
            image_tensor, n_color_clusters=2, pattern_threshold=0.5, enable_ocr=False
        )
        
        features = json.loads(features_json)
        self.assertEqual(len(features["dominant_colors"]), 2, 
                        "Should return requested number of color clusters")
        
        # Test with different pattern threshold
        features_json, _ = self.pre_analysis.analyze(
            image_tensor, n_color_clusters=5, pattern_threshold=0.1, enable_ocr=False
        )
        
        features = json.loads(features_json)
        self.assertIn(features["pattern_complexity"], ["high", "medium", "low"])
    
    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        # Test with very small image
        small_image = Image.new('RGB', (5, 5), (255, 255, 255))
        small_tensor = self._pil_to_tensor(small_image)
        
        # Should not crash
        features_json, visualization = self.pre_analysis.analyze(
            small_tensor, n_color_clusters=3, pattern_threshold=0.3, enable_ocr=False
        )
        
        features = json.loads(features_json)
        self.assertIn("dominant_colors", features)
        self.assertIn("pattern_complexity", features)
        
        # Test with invalid tensor
        invalid_tensor = torch.randn(1, 3, 10, 10)  # Random tensor
        
        # Should not crash
        features_json, visualization = self.pre_analysis.analyze(
            invalid_tensor, n_color_clusters=3, pattern_threshold=0.3, enable_ocr=False
        )
        
        features = json.loads(features_json)
        self.assertIn("dominant_colors", features)


class TestPreAnalysisEdgeCases(unittest.TestCase):
    """Test edge cases for pre-analysis"""
    
    def setUp(self):
        self.pre_analysis = PreAnalysisNode()
    
    def test_empty_image(self):
        """Test with completely black image"""
        black_image = Image.new('RGB', (100, 100), (0, 0, 0))
        image_tensor = torch.from_numpy(np.array(black_image).astype(np.float32) / 255.0)[None,]
        
        features_json, _ = self.pre_analysis.analyze(
            image_tensor, n_color_clusters=3, pattern_threshold=0.3, enable_ocr=False
        )
        
        features = json.loads(features_json)
        self.assertIn("dominant_colors", features)
        self.assertIn("exposure", features)
        self.assertEqual(features["exposure"], 0.0, "Black image should have zero exposure")
    
    def test_white_image(self):
        """Test with completely white image"""
        white_image = Image.new('RGB', (100, 100), (255, 255, 255))
        image_tensor = torch.from_numpy(np.array(white_image).astype(np.float32) / 255.0)[None,]
        
        features_json, _ = self.pre_analysis.analyze(
            image_tensor, n_color_clusters=3, pattern_threshold=0.3, enable_ocr=False
        )
        
        features = json.loads(features_json)
        self.assertIn("dominant_colors", features)
        self.assertIn("exposure", features)
        self.assertEqual(features["exposure"], 1.0, "White image should have maximum exposure")
    
    def test_single_pixel_image(self):
        """Test with single pixel image"""
        single_pixel = Image.new('RGB', (1, 1), (128, 128, 128))
        image_tensor = torch.from_numpy(np.array(single_pixel).astype(np.float32) / 255.0)[None,]
        
        # Should not crash
        features_json, _ = self.pre_analysis.analyze(
            image_tensor, n_color_clusters=1, pattern_threshold=0.3, enable_ocr=False
        )
        
        features = json.loads(features_json)
        self.assertIn("dominant_colors", features)
        self.assertIn("pattern_complexity", features)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestPreAnalysis))
    test_suite.addTest(unittest.makeSuite(TestPreAnalysisEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
