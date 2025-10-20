"""
Unit tests for mask quality scoring in Phase 2.1
Tests edge alignment, entropy, and morphological stability metrics
"""

import unittest
import numpy as np
import cv2
from PIL import Image
import torch
import sys
import os

# Add the ComfyUI custom_nodes directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ComfyUI', 'custom_nodes'))

from advanced_garment_segmentation import AdvancedGarmentSegmentation


class TestMaskQuality(unittest.TestCase):
    """Test mask quality scoring functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.segmentation = AdvancedGarmentSegmentation()
        
        # Create test images and masks
        self.test_image = self._create_test_image()
        self.test_mask = self._create_test_mask()
        self.test_mask_poor = self._create_poor_quality_mask()
    
    def _create_test_image(self):
        """Create a test image with clear edges"""
        # Create a 100x100 image with a centered rectangle
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[25:75, 25:75] = [255, 255, 255]  # White rectangle
        return Image.fromarray(image)
    
    def _create_test_mask(self):
        """Create a high-quality mask"""
        # Create a clean mask matching the test image
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 255  # White rectangle
        return Image.fromarray(mask, mode='L')
    
    def _create_poor_quality_mask(self):
        """Create a poor-quality mask with noise and blur"""
        # Create a noisy, blurred mask
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 255  # Base rectangle
        
        # Add noise
        noise = np.random.randint(0, 50, (100, 100), dtype=np.uint8)
        mask = np.clip(mask.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Blur the mask
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return Image.fromarray(mask, mode='L')
    
    def test_edge_alignment_good_mask(self):
        """Test edge alignment calculation with good quality mask"""
        edge_score = self.segmentation._compute_edge_alignment(self.test_mask, self.test_image)
        
        # Good mask should have high edge alignment
        self.assertGreater(edge_score, 0.7, "Good mask should have high edge alignment")
        self.assertLessEqual(edge_score, 1.0, "Edge alignment should not exceed 1.0")
    
    def test_edge_alignment_poor_mask(self):
        """Test edge alignment calculation with poor quality mask"""
        edge_score = self.segmentation._compute_edge_alignment(self.test_mask_poor, self.test_image)
        
        # Poor mask should have lower edge alignment
        self.assertLess(edge_score, 0.7, "Poor mask should have lower edge alignment")
        self.assertGreaterEqual(edge_score, 0.0, "Edge alignment should not be negative")
    
    def test_mask_entropy_good_mask(self):
        """Test mask entropy calculation with good quality mask"""
        entropy_score = self.segmentation._compute_mask_entropy(self.test_mask)
        
        # Good mask (mostly binary) should have low entropy
        self.assertGreater(entropy_score, 0.5, "Good mask should have reasonable entropy score")
        self.assertLessEqual(entropy_score, 1.0, "Entropy score should not exceed 1.0")
    
    def test_mask_entropy_poor_mask(self):
        """Test mask entropy calculation with poor quality mask"""
        entropy_score = self.segmentation._compute_mask_entropy(self.test_mask_poor)
        
        # Poor mask (noisy) should have different entropy characteristics
        self.assertGreaterEqual(entropy_score, 0.0, "Entropy score should not be negative")
        self.assertLessEqual(entropy_score, 1.0, "Entropy score should not exceed 1.0")
    
    def test_morphological_stability_good_mask(self):
        """Test morphological stability with good quality mask"""
        stability_score = self.segmentation._compute_morphological_stability(self.test_mask)
        
        # Good mask should be morphologically stable
        self.assertGreater(stability_score, 0.8, "Good mask should be morphologically stable")
        self.assertLessEqual(stability_score, 1.0, "Stability score should not exceed 1.0")
    
    def test_morphological_stability_poor_mask(self):
        """Test morphological stability with poor quality mask"""
        stability_score = self.segmentation._compute_morphological_stability(self.test_mask_poor)
        
        # Poor mask should be less stable
        self.assertGreaterEqual(stability_score, 0.0, "Stability score should not be negative")
        self.assertLessEqual(stability_score, 1.0, "Stability score should not exceed 1.0")
    
    def test_compute_mask_quality_integration(self):
        """Test the complete mask quality computation"""
        # Create dummy masks for the full computation
        rmbg_mask = self.test_mask
        u2net_mask = self.test_mask
        combined_mask = self.test_mask
        
        confidence, quality_metrics = self.segmentation._compute_mask_quality(
            rmbg_mask, u2net_mask, combined_mask, self.test_image
        )
        
        # Check that all required metrics are present
        required_metrics = [
            "mask_quality_score", "edge_alignment", "mask_entropy", 
            "stability", "mask_weights"
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, quality_metrics, f"Missing metric: {metric}")
        
        # Check metric ranges
        self.assertGreaterEqual(quality_metrics["mask_quality_score"], 0.0)
        self.assertLessEqual(quality_metrics["mask_quality_score"], 1.0)
        
        # Check mask weights sum to approximately 1.0
        weights = quality_metrics["mask_weights"]
        weight_sum = sum(weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=2, 
                              msg="Mask weights should sum to 1.0")
    
    def test_mask_quality_error_handling(self):
        """Test error handling in mask quality computation"""
        # Test with invalid input
        invalid_mask = Image.new('L', (10, 10), 0)  # Very small mask
        invalid_image = Image.new('RGB', (100, 100), (255, 255, 255))  # Different size
        
        # Should not crash and should return default values
        edge_score = self.segmentation._compute_edge_alignment(invalid_mask, invalid_image)
        self.assertGreaterEqual(edge_score, 0.0)
        self.assertLessEqual(edge_score, 1.0)
        
        entropy_score = self.segmentation._compute_mask_entropy(invalid_mask)
        self.assertGreaterEqual(entropy_score, 0.0)
        self.assertLessEqual(entropy_score, 1.0)
        
        stability_score = self.segmentation._compute_morphological_stability(invalid_mask)
        self.assertGreaterEqual(stability_score, 0.0)
        self.assertLessEqual(stability_score, 1.0)
    
    def test_mask_quality_consistency(self):
        """Test that mask quality computation is consistent"""
        # Run the same computation multiple times
        results = []
        for _ in range(5):
            confidence, quality_metrics = self.segmentation._compute_mask_quality(
                self.test_mask, self.test_mask, self.test_mask, self.test_image
            )
            results.append((confidence, quality_metrics["mask_quality_score"]))
        
        # Results should be consistent (within small tolerance for floating point)
        confidences = [r[0] for r in results]
        quality_scores = [r[1] for r in results]
        
        self.assertAlmostEqual(max(confidences), min(confidences), places=3,
                              msg="Confidence scores should be consistent")
        self.assertAlmostEqual(max(quality_scores), min(quality_scores), places=3,
                              msg="Quality scores should be consistent")


class TestMaskQualityEdgeCases(unittest.TestCase):
    """Test edge cases for mask quality scoring"""
    
    def setUp(self):
        self.segmentation = AdvancedGarmentSegmentation()
    
    def test_empty_mask(self):
        """Test with completely empty mask"""
        empty_mask = Image.new('L', (100, 100), 0)
        test_image = Image.new('RGB', (100, 100), (255, 255, 255))
        
        edge_score = self.segmentation._compute_edge_alignment(empty_mask, test_image)
        self.assertEqual(edge_score, 0.0, "Empty mask should have zero edge alignment")
        
        entropy_score = self.segmentation._compute_mask_entropy(empty_mask)
        self.assertGreaterEqual(entropy_score, 0.0)
        
        stability_score = self.segmentation._compute_morphological_stability(empty_mask)
        self.assertGreaterEqual(stability_score, 0.0)
    
    def test_full_mask(self):
        """Test with completely filled mask"""
        full_mask = Image.new('L', (100, 100), 255)
        test_image = Image.new('RGB', (100, 100), (255, 255, 255))
        
        edge_score = self.segmentation._compute_edge_alignment(full_mask, test_image)
        self.assertGreaterEqual(edge_score, 0.0)
        
        entropy_score = self.segmentation._compute_mask_entropy(full_mask)
        self.assertGreaterEqual(entropy_score, 0.0)
        
        stability_score = self.segmentation._compute_morphological_stability(full_mask)
        self.assertGreaterEqual(stability_score, 0.0)
    
    def test_single_pixel_mask(self):
        """Test with single pixel mask"""
        single_pixel_mask = Image.new('L', (100, 100), 0)
        single_pixel_mask.putpixel((50, 50), 255)
        test_image = Image.new('RGB', (100, 100), (255, 255, 255))
        
        # Should not crash
        edge_score = self.segmentation._compute_edge_alignment(single_pixel_mask, test_image)
        self.assertGreaterEqual(edge_score, 0.0)
        
        entropy_score = self.segmentation._compute_mask_entropy(single_pixel_mask)
        self.assertGreaterEqual(entropy_score, 0.0)
        
        stability_score = self.segmentation._compute_morphological_stability(single_pixel_mask)
        self.assertGreaterEqual(stability_score, 0.0)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestMaskQuality))
    test_suite.addTest(unittest.makeSuite(TestMaskQualityEdgeCases))
    
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
