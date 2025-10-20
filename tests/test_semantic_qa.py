"""
Integration tests for semantic QA in Phase 2.1
Tests Gemini-based semantic alignment verification
"""

import unittest
import numpy as np
import cv2
from PIL import Image
import torch
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the ComfyUI custom_nodes directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ComfyUI', 'custom_nodes'))

from semantic_qa_node import SemanticQANode


class TestSemanticQA(unittest.TestCase):
    """Test semantic QA functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.semantic_qa = SemanticQANode()
        
        # Create test images and facts
        self.test_image = self._create_test_image()
        self.test_facts = self._create_test_facts()
        self.test_facts_json = json.dumps(self.test_facts)
    
    def _create_test_image(self):
        """Create a test garment image"""
        # Create a simple garment-like image
        image = np.full((200, 200, 3), [240, 240, 240], dtype=np.uint8)  # Light gray background
        
        # Add a simple garment shape (rectangle)
        image[50:150, 75:125] = [100, 150, 200]  # Blue garment
        
        return Image.fromarray(image)
    
    def _create_test_facts(self):
        """Create test Facts V3.1 data"""
        return {
            "schema_version": "3.1",
            "analysis_mode": "full",
            "garment": {
                "category": "dress_shirt",
                "color_hex": "#6496C8",
                "color_name": "blue",
                "pattern": "solid",
                "transparency_level": 0.0,
                "complexity_score": 0.3,
                "parts": [
                    {
                        "part_name": "body",
                        "color_hex": "#6496C8",
                        "texture": "woven",
                        "pattern": "solid",
                        "condition": "clean",
                        "seam_quality": 0.8,
                        "sharpness_needed": 0.7,
                        "transparency": 0.0,
                        "analyzed": True,
                        "analysis_method": "gemini"
                    }
                ]
            },
            "photography": {
                "bg": "pure_white",
                "lighting": "soft_even_high_key",
                "frame": "4:5",
                "coverage_pct": 85
            },
            "routing": {
                "suggested_model": "sdxl",
                "use_ip_adapter": False,
                "use_controlnet_inpaint": True
            },
            "risk_score": 0.2
        }
    
    def _pil_to_tensor(self, image):
        """Convert PIL image to ComfyUI tensor format"""
        image_np = np.array(image).astype(np.float32) / 255.0
        return torch.from_numpy(image_np)[None,]
    
    def test_color_delta_e_calculation(self):
        """Test ΔE color difference calculation"""
        # Test with identical colors
        delta_e = self.semantic_qa._color_delta_e("#6496C8", "#6496C8")
        self.assertAlmostEqual(delta_e, 0.0, places=1, 
                              msg="Identical colors should have ΔE ≈ 0")
        
        # Test with different colors
        delta_e = self.semantic_qa._color_delta_e("#000000", "#FFFFFF")
        self.assertGreater(delta_e, 50.0, 
                          msg="Black and white should have high ΔE")
        
        # Test with similar colors
        delta_e = self.semantic_qa._color_delta_e("#6496C8", "#6496C9")
        self.assertLess(delta_e, 5.0, 
                       msg="Similar colors should have low ΔE")
    
    def test_pattern_similarity(self):
        """Test pattern similarity detection"""
        # Test identical patterns
        self.assertTrue(self.semantic_qa._patterns_similar("solid", "solid"))
        self.assertTrue(self.semantic_qa._patterns_similar("striped", "stripes"))
        self.assertTrue(self.semantic_qa._patterns_similar("printed", "print"))
        
        # Test different patterns
        self.assertFalse(self.semantic_qa._patterns_similar("solid", "striped"))
        self.assertFalse(self.semantic_qa._patterns_similar("printed", "textured"))
        
        # Test case insensitive
        self.assertTrue(self.semantic_qa._patterns_similar("SOLID", "solid"))
    
    def test_category_similarity(self):
        """Test garment category similarity detection"""
        # Test identical categories
        self.assertTrue(self.semantic_qa._categories_similar("dress_shirt", "dress_shirt"))
        self.assertTrue(self.semantic_qa._categories_similar("shirt", "button_up"))
        self.assertTrue(self.semantic_qa._categories_similar("t_shirt", "tee"))
        
        # Test different categories
        self.assertFalse(self.semantic_qa._categories_similar("dress_shirt", "pants"))
        self.assertFalse(self.semantic_qa._categories_similar("shirt", "jacket"))
        
        # Test case insensitive
        self.assertTrue(self.semantic_qa._categories_similar("DRESS_SHIRT", "dress_shirt"))
    
    def test_alignment_computation(self):
        """Test semantic alignment computation"""
        # Create mock Gemini facts that match original facts
        gemini_facts = {
            "category": "dress_shirt",
            "color_hex": "#6496C8",
            "pattern": "solid",
            "key_features": ["collar", "sleeves"],
            "quality_score": 0.8,
            "completeness": 0.9
        }
        
        alignment = self.semantic_qa._compute_alignment(gemini_facts, self.test_facts)
        
        self.assertGreaterEqual(alignment, 0.0, "Alignment should not be negative")
        self.assertLessEqual(alignment, 1.0, "Alignment should not exceed 1.0")
        self.assertGreater(alignment, 0.7, "Matching facts should have high alignment")
    
    def test_alignment_computation_mismatch(self):
        """Test semantic alignment with mismatched facts"""
        # Create mock Gemini facts that don't match original facts
        gemini_facts = {
            "category": "pants",
            "color_hex": "#FF0000",
            "pattern": "striped",
            "key_features": ["pockets"],
            "quality_score": 0.5,
            "completeness": 0.6
        }
        
        alignment = self.semantic_qa._compute_alignment(gemini_facts, self.test_facts)
        
        self.assertGreaterEqual(alignment, 0.0, "Alignment should not be negative")
        self.assertLessEqual(alignment, 1.0, "Alignment should not exceed 1.0")
        self.assertLess(alignment, 0.5, "Mismatched facts should have low alignment")
    
    @patch('semantic_qa_node.genai')
    def test_gemini_analysis_success(self, mock_genai):
        """Test successful Gemini analysis"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '''
        {
            "category": "dress_shirt",
            "color_hex": "#6496C8",
            "pattern": "solid",
            "key_features": ["collar", "sleeves", "buttons"],
            "quality_score": 0.8,
            "completeness": 0.9,
            "notes": "Clean blue dress shirt"
        }
        '''
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Temporarily enable Gemini
        original_available = self.semantic_qa.gemini_available
        self.semantic_qa.gemini_available = True
        self.semantic_qa.model = mock_model
        
        try:
            gemini_facts, alignment = self.semantic_qa._analyze_with_gemini(
                self.test_image, self.test_facts
            )
            
            self.assertIsInstance(gemini_facts, dict, "Should return dictionary")
            self.assertIn("category", gemini_facts)
            self.assertIn("color_hex", gemini_facts)
            self.assertIn("pattern", gemini_facts)
            
            self.assertGreaterEqual(alignment, 0.0)
            self.assertLessEqual(alignment, 1.0)
            
            # Verify Gemini was called
            mock_model.generate_content.assert_called_once()
        finally:
            self.semantic_qa.gemini_available = original_available
    
    def test_fallback_analysis(self):
        """Test fallback analysis when Gemini is not available"""
        # Disable Gemini
        original_available = self.semantic_qa.gemini_available
        self.semantic_qa.gemini_available = False
        
        try:
            gemini_facts, alignment = self.semantic_qa._fallback_analysis(
                self.test_image, self.test_facts
            )
            
            self.assertIsInstance(gemini_facts, dict, "Should return dictionary")
            self.assertIn("category", gemini_facts)
            self.assertIn("color_hex", gemini_facts)
            self.assertIn("pattern", gemini_facts)
            self.assertIn("notes", gemini_facts)
            self.assertEqual(gemini_facts["notes"], "Fallback analysis - Gemini not available")
            
            self.assertGreaterEqual(alignment, 0.0)
            self.assertLessEqual(alignment, 1.0)
        finally:
            self.semantic_qa.gemini_available = original_available
    
    def test_verify_alignment_integration(self):
        """Test the complete verify_alignment workflow"""
        image_tensor = self._pil_to_tensor(self.test_image)
        
        # Test with high alignment threshold
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                image_tensor, self.test_facts_json, 
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        
        # Check return types and ranges
        self.assertIsInstance(semantic_alignment, float)
        self.assertGreaterEqual(semantic_alignment, 0.0)
        self.assertLessEqual(semantic_alignment, 1.0)
        
        self.assertIsInstance(gemini_facts_json, str)
        self.assertIsInstance(qa_report_json, str)
        self.assertIsInstance(should_rerender, bool)
        
        # Parse JSON outputs
        gemini_facts = json.loads(gemini_facts_json)
        qa_report = json.loads(qa_report_json)
        
        # Check gemini facts structure
        self.assertIn("category", gemini_facts)
        self.assertIn("color_hex", gemini_facts)
        self.assertIn("pattern", gemini_facts)
        
        # Check QA report structure
        self.assertIn("semantic_alignment", qa_report)
        self.assertIn("alignment_threshold", qa_report)
        self.assertIn("passed", qa_report)
        self.assertIn("should_rerender", qa_report)
        
        # Check logic consistency
        self.assertEqual(qa_report["semantic_alignment"], semantic_alignment)
        self.assertEqual(qa_report["should_rerender"], should_rerender)
        
        if semantic_alignment < 0.9:
            self.assertTrue(should_rerender, "Should re-render if alignment below threshold")
        else:
            self.assertFalse(should_rerender, "Should not re-render if alignment above threshold")
    
    def test_verify_alignment_with_different_thresholds(self):
        """Test verify_alignment with different threshold settings"""
        image_tensor = self._pil_to_tensor(self.test_image)
        
        # Test with low threshold (should not trigger re-render)
        _, _, _, should_rerender_low = self.semantic_qa.verify_alignment(
            image_tensor, self.test_facts_json, 
            alignment_threshold=0.5, enable_auto_rerender=True
        )
        
        # Test with high threshold (might trigger re-render)
        _, _, _, should_rerender_high = self.semantic_qa.verify_alignment(
            image_tensor, self.test_facts_json, 
            alignment_threshold=0.95, enable_auto_rerender=True
        )
        
        # Test with auto re-render disabled
        _, _, _, should_rerender_disabled = self.semantic_qa.verify_alignment(
            image_tensor, self.test_facts_json, 
            alignment_threshold=0.5, enable_auto_rerender=False
        )
        
        self.assertFalse(should_rerender_disabled, 
                        "Should not re-render when auto re-render is disabled")
    
    def test_error_handling_invalid_facts(self):
        """Test error handling with invalid facts JSON"""
        image_tensor = self._pil_to_tensor(self.test_image)
        invalid_facts_json = "invalid json"
        
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                image_tensor, invalid_facts_json, 
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        
        # Should return error response
        self.assertEqual(semantic_alignment, 0.0)
        self.assertFalse(should_rerender)
        
        # Check error in response
        qa_report = json.loads(qa_report_json)
        self.assertIn("error", qa_report)
    
    def test_error_handling_invalid_image(self):
        """Test error handling with invalid image"""
        invalid_tensor = torch.randn(1, 3, 10, 10)  # Random tensor
        
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                invalid_tensor, self.test_facts_json, 
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        
        # Should handle gracefully
        self.assertGreaterEqual(semantic_alignment, 0.0)
        self.assertLessEqual(semantic_alignment, 1.0)
        self.assertIsInstance(should_rerender, bool)


class TestSemanticQAEdgeCases(unittest.TestCase):
    """Test edge cases for semantic QA"""
    
    def setUp(self):
        self.semantic_qa = SemanticQANode()
    
    def test_empty_facts(self):
        """Test with empty facts"""
        empty_facts = {}
        empty_facts_json = json.dumps(empty_facts)
        
        test_image = Image.new('RGB', (100, 100), (255, 255, 255))
        image_tensor = torch.from_numpy(np.array(test_image).astype(np.float32) / 255.0)[None,]
        
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                image_tensor, empty_facts_json, 
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        
        # Should handle gracefully
        self.assertGreaterEqual(semantic_alignment, 0.0)
        self.assertLessEqual(semantic_alignment, 1.0)
        self.assertIsInstance(should_rerender, bool)
    
    def test_missing_color_information(self):
        """Test alignment computation when color information is missing"""
        facts_without_color = {
            "garment": {
                "category": "dress_shirt",
                "pattern": "solid"
                # Missing color_hex
            }
        }
        
        gemini_facts = {
            "category": "dress_shirt",
            "color_hex": "#6496C8",
            "pattern": "solid"
        }
        
        alignment = self.semantic_qa._compute_alignment(gemini_facts, facts_without_color)
        
        # Should still compute alignment for available fields
        self.assertGreaterEqual(alignment, 0.0)
        self.assertLessEqual(alignment, 1.0)
    
    def test_invalid_hex_colors(self):
        """Test with invalid hex color formats"""
        # Should handle gracefully
        delta_e = self.semantic_qa._color_delta_e("invalid", "#6496C8")
        self.assertGreaterEqual(delta_e, 0.0)
        
        delta_e = self.semantic_qa._color_delta_e("#6496C8", "invalid")
        self.assertGreaterEqual(delta_e, 0.0)
        
        delta_e = self.semantic_qa._color_delta_e("invalid", "invalid")
        self.assertGreaterEqual(delta_e, 0.0)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestSemanticQA))
    test_suite.addTest(unittest.makeSuite(TestSemanticQAEdgeCases))
    
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
