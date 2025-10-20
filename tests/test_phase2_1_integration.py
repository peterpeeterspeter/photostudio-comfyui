"""
Integration tests for Phase 2.1 enhancements
Tests the complete pipeline with pre-analysis, mask quality, and semantic QA
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

from pre_analysis_node import PreAnalysisNode
from advanced_garment_segmentation import AdvancedGarmentSegmentation
from semantic_qa_node import SemanticQANode
from garment_part_segmentation import GarmentPartSegmentation


class TestPhase21Integration(unittest.TestCase):
    """Test Phase 2.1 integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pre_analysis = PreAnalysisNode()
        self.segmentation = AdvancedGarmentSegmentation()
        self.semantic_qa = SemanticQANode()
        self.part_segmentation = GarmentPartSegmentation()
        
        # Create test image
        self.test_image = self._create_test_garment_image()
        self.test_image_tensor = self._pil_to_tensor(self.test_image)
        
        # Create test facts
        self.test_facts = self._create_test_facts()
        self.test_facts_json = json.dumps(self.test_facts)
    
    def _create_test_garment_image(self):
        """Create a realistic test garment image"""
        # Create a 400x600 image (4:5 aspect ratio)
        image = np.full((600, 400, 3), [240, 240, 240], dtype=np.uint8)  # Light gray background
        
        # Add garment shape (dress shirt)
        # Body
        image[100:500, 150:250] = [100, 150, 200]  # Blue body
        
        # Collar
        image[100:150, 180:220] = [120, 170, 220]  # Slightly different blue collar
        
        # Sleeves
        image[120:200, 120:150] = [100, 150, 200]  # Left sleeve
        image[120:200, 250:280] = [100, 150, 200]  # Right sleeve
        
        # Add some texture/noise to make it more realistic
        noise = np.random.randint(-10, 10, image.shape, dtype=np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return Image.fromarray(image)
    
    def _create_test_facts(self):
        """Create comprehensive test Facts V3.1 data"""
        return {
            "schema_version": "3.1",
            "analysis_mode": "full",
            "garment": {
                "category": "dress_shirt",
                "silhouette": "classic_fit",
                "fabric": "cotton",
                "color_hex": "#6496C8",
                "color_name": "blue",
                "pattern": "solid",
                "transparency_level": 0.0,
                "complexity_score": 0.4,
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
                    },
                    {
                        "part_name": "collar",
                        "color_hex": "#78AAF0",
                        "texture": "woven",
                        "pattern": "solid",
                        "condition": "clean",
                        "seam_quality": 0.9,
                        "sharpness_needed": 0.8,
                        "transparency": 0.0,
                        "analyzed": True,
                        "analysis_method": "gemini"
                    },
                    {
                        "part_name": "sleeve",
                        "color_hex": "#6496C8",
                        "texture": "woven",
                        "pattern": "solid",
                        "condition": "clean",
                        "seam_quality": 0.7,
                        "sharpness_needed": 0.6,
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
    
    def test_pre_analysis_pipeline(self):
        """Test pre-analysis feature extraction"""
        # Run pre-analysis
        pre_features_json, debug_image = self.pre_analysis.analyze(
            self.test_image_tensor, n_color_clusters=5, pattern_threshold=0.3, enable_ocr=True
        )
        
        # Parse results
        pre_features = json.loads(pre_features_json)
        
        # Verify all required features are present
        required_features = [
            "dominant_colors", "pattern_complexity", "text_detected", 
            "text_boxes", "exposure", "contrast"
        ]
        
        for feature in required_features:
            self.assertIn(feature, pre_features, f"Missing pre-analysis feature: {feature}")
        
        # Verify feature quality
        self.assertGreater(len(pre_features["dominant_colors"]), 0, 
                          "Should detect dominant colors")
        self.assertIn(pre_features["pattern_complexity"], ["high", "medium", "low"],
                     "Should have valid pattern complexity")
        self.assertIsInstance(pre_features["text_detected"], bool,
                             "Text detection should be boolean")
        self.assertGreaterEqual(pre_features["exposure"], 0.0,
                               "Exposure should be non-negative")
        self.assertLessEqual(pre_features["exposure"], 1.0,
                            "Exposure should not exceed 1.0")
        
        # Verify debug image
        self.assertIsInstance(debug_image, torch.Tensor,
                             "Debug image should be a tensor")
        self.assertEqual(len(debug_image.shape), 4,
                        "Debug image should have 4 dimensions")
    
    def test_advanced_segmentation_pipeline(self):
        """Test advanced garment segmentation with quality scoring"""
        # Run segmentation
        garment_only, garment_mask, confidence, quality_metrics_json = \
            self.segmentation.segment_garment(
                self.test_image_tensor, rmbg_threshold=0.32, u2net_threshold=0.35,
                use_human_subtract=True, mask_blur=3, edge_feather=4
            )
        
        # Verify outputs
        self.assertIsInstance(garment_only, torch.Tensor,
                             "Garment-only image should be a tensor")
        self.assertIsInstance(garment_mask, torch.Tensor,
                             "Garment mask should be a tensor")
        self.assertIsInstance(confidence, float,
                             "Confidence should be a float")
        self.assertIsInstance(quality_metrics_json, str,
                             "Quality metrics should be a JSON string")
        
        # Verify confidence range
        self.assertGreaterEqual(confidence, 0.0,
                               "Confidence should be non-negative")
        self.assertLessEqual(confidence, 1.0,
                            "Confidence should not exceed 1.0")
        
        # Parse quality metrics
        quality_metrics = json.loads(quality_metrics_json)
        
        # Verify quality metrics structure
        required_metrics = [
            "mask_quality_score", "edge_alignment", "mask_entropy", 
            "stability", "mask_weights"
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, quality_metrics, f"Missing quality metric: {metric}")
        
        # Verify metric ranges
        for metric in ["mask_quality_score", "edge_alignment", "mask_entropy", "stability"]:
            self.assertGreaterEqual(quality_metrics[metric], 0.0,
                                   f"{metric} should be non-negative")
            self.assertLessEqual(quality_metrics[metric], 1.0,
                                f"{metric} should not exceed 1.0")
        
        # Verify mask weights
        weights = quality_metrics["mask_weights"]
        self.assertIn("rmbg", weights)
        self.assertIn("u2net", weights)
        weight_sum = sum(weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=2,
                              msg="Mask weights should sum to 1.0")
    
    def test_dynamic_prompts_generation(self):
        """Test dynamic prompts generation from Facts V3.1"""
        # Test with high interior visibility
        facts_high_visibility = self.test_facts.copy()
        facts_high_visibility["interior_visibility"] = {"level": "high"}
        
        parts_list = self.part_segmentation._build_dynamic_prompts(facts_high_visibility)
        
        self.assertIsInstance(parts_list, list,
                             "Dynamic prompts should be a list")
        self.assertGreater(len(parts_list), 0,
                          "Should generate at least one part prompt")
        
        # Should include additional parts for high interior visibility
        expected_parts = ["collar", "sleeve", "body", "hem"]
        for part in expected_parts:
            self.assertIn(part, parts_list,
                         f"Should include {part} in dynamic prompts")
        
        # Test with high complexity
        facts_high_complexity = self.test_facts.copy()
        facts_high_complexity["garment"]["complexity_score"] = 0.8
        
        parts_list = self.part_segmentation._build_dynamic_prompts(facts_high_complexity)
        
        # Should include additional parts for high complexity
        self.assertGreater(len(parts_list), 4,
                          "High complexity should generate more parts")
    
    def test_semantic_qa_pipeline(self):
        """Test semantic QA verification"""
        # Create a rendered image (simulate generation output)
        rendered_image = self.test_image.copy()
        # Modify slightly to simulate generation
        rendered_array = np.array(rendered_image)
        rendered_array[100:200, 150:250] = [110, 160, 210]  # Slightly different blue
        rendered_image = Image.fromarray(rendered_array)
        rendered_tensor = self._pil_to_tensor(rendered_image)
        
        # Run semantic QA
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                rendered_tensor, self.test_facts_json,
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        
        # Verify outputs
        self.assertIsInstance(semantic_alignment, float,
                             "Semantic alignment should be a float")
        self.assertGreaterEqual(semantic_alignment, 0.0,
                               "Semantic alignment should be non-negative")
        self.assertLessEqual(semantic_alignment, 1.0,
                            "Semantic alignment should not exceed 1.0")
        
        self.assertIsInstance(gemini_facts_json, str,
                             "Gemini facts should be a JSON string")
        self.assertIsInstance(qa_report_json, str,
                             "QA report should be a JSON string")
        self.assertIsInstance(should_rerender, bool,
                             "Should re-render should be a boolean")
        
        # Parse JSON outputs
        gemini_facts = json.loads(gemini_facts_json)
        qa_report = json.loads(qa_report_json)
        
        # Verify gemini facts structure
        self.assertIn("category", gemini_facts)
        self.assertIn("color_hex", gemini_facts)
        self.assertIn("pattern", gemini_facts)
        
        # Verify QA report structure
        self.assertIn("semantic_alignment", qa_report)
        self.assertIn("alignment_threshold", qa_report)
        self.assertIn("passed", qa_report)
        self.assertIn("should_rerender", qa_report)
    
    def test_complete_pipeline_integration(self):
        """Test the complete Phase 2.1 pipeline integration"""
        # Step 1: Pre-analysis
        pre_features_json, debug_image = self.pre_analysis.analyze(
            self.test_image_tensor, n_color_clusters=5, pattern_threshold=0.3, enable_ocr=True
        )
        pre_features = json.loads(pre_features_json)
        
        # Step 2: Advanced segmentation with quality scoring
        garment_only, garment_mask, confidence, quality_metrics_json = \
            self.segmentation.segment_garment(
                self.test_image_tensor, rmbg_threshold=0.32, u2net_threshold=0.35,
                use_human_subtract=True, mask_blur=3, edge_feather=4
            )
        quality_metrics = json.loads(quality_metrics_json)
        
        # Step 3: Dynamic prompts generation
        parts_list = self.part_segmentation._build_dynamic_prompts(self.test_facts)
        
        # Step 4: Part segmentation (simplified test)
        # Note: This would normally use GroundingDINO + SAM2, but we'll test the interface
        self.assertIsInstance(parts_list, list)
        self.assertGreater(len(parts_list), 0)
        
        # Step 5: Semantic QA (simulate with a slightly modified image)
        rendered_image = self.test_image.copy()
        rendered_array = np.array(rendered_image)
        rendered_array[100:200, 150:250] = [110, 160, 210]  # Slightly different
        rendered_image = Image.fromarray(rendered_array)
        rendered_tensor = self._pil_to_tensor(rendered_image)
        
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                rendered_tensor, self.test_facts_json,
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        
        # Verify pipeline integration
        self.assertIsInstance(pre_features, dict)
        self.assertIsInstance(quality_metrics, dict)
        self.assertIsInstance(parts_list, list)
        self.assertIsInstance(semantic_alignment, float)
        
        # Verify data flow consistency
        # Pre-analysis should inform segmentation quality
        self.assertIn("mask_quality_score", quality_metrics)
        
        # Quality metrics should inform semantic QA
        self.assertGreaterEqual(semantic_alignment, 0.0)
        self.assertLessEqual(semantic_alignment, 1.0)
        
        # Dynamic prompts should be contextually appropriate
        self.assertGreater(len(parts_list), 0)
        
        print(f"\nPipeline Integration Results:")
        print(f"  Pre-analysis: {len(pre_features['dominant_colors'])} colors, "
              f"complexity={pre_features['pattern_complexity']}")
        print(f"  Segmentation: confidence={confidence:.3f}, "
              f"quality={quality_metrics['mask_quality_score']:.3f}")
        print(f"  Dynamic prompts: {len(parts_list)} parts")
        print(f"  Semantic QA: alignment={semantic_alignment:.3f}, "
              f"re-render={should_rerender}")
    
    def test_error_handling_integration(self):
        """Test error handling across the pipeline"""
        # Test with invalid image
        invalid_tensor = torch.randn(1, 3, 10, 10)  # Random tensor
        
        # Pre-analysis should handle gracefully
        pre_features_json, debug_image = self.pre_analysis.analyze(
            invalid_tensor, n_color_clusters=3, pattern_threshold=0.3, enable_ocr=False
        )
        pre_features = json.loads(pre_features_json)
        self.assertIn("dominant_colors", pre_features)
        
        # Segmentation should handle gracefully
        garment_only, garment_mask, confidence, quality_metrics_json = \
            self.segmentation.segment_garment(
                invalid_tensor, rmbg_threshold=0.32, u2net_threshold=0.35,
                use_human_subtract=True, mask_blur=3, edge_feather=4
            )
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        
        # Semantic QA should handle gracefully
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                invalid_tensor, self.test_facts_json,
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        self.assertIsInstance(semantic_alignment, float)
        self.assertGreaterEqual(semantic_alignment, 0.0)
    
    def test_performance_benchmarks(self):
        """Test performance characteristics of the pipeline"""
        import time
        
        # Benchmark pre-analysis
        start_time = time.time()
        pre_features_json, debug_image = self.pre_analysis.analyze(
            self.test_image_tensor, n_color_clusters=5, pattern_threshold=0.3, enable_ocr=False
        )
        pre_analysis_time = time.time() - start_time
        
        # Benchmark segmentation
        start_time = time.time()
        garment_only, garment_mask, confidence, quality_metrics_json = \
            self.segmentation.segment_garment(
                self.test_image_tensor, rmbg_threshold=0.32, u2net_threshold=0.35,
                use_human_subtract=True, mask_blur=3, edge_feather=4
            )
        segmentation_time = time.time() - start_time
        
        # Benchmark semantic QA
        start_time = time.time()
        semantic_alignment, gemini_facts_json, qa_report_json, should_rerender = \
            self.semantic_qa.verify_alignment(
                self.test_image_tensor, self.test_facts_json,
                alignment_threshold=0.9, enable_auto_rerender=True
            )
        semantic_qa_time = time.time() - start_time
        
        # Verify reasonable performance (adjust thresholds as needed)
        self.assertLess(pre_analysis_time, 5.0, "Pre-analysis should complete within 5 seconds")
        self.assertLess(segmentation_time, 10.0, "Segmentation should complete within 10 seconds")
        self.assertLess(semantic_qa_time, 3.0, "Semantic QA should complete within 3 seconds")
        
        print(f"\nPerformance Benchmarks:")
        print(f"  Pre-analysis: {pre_analysis_time:.2f}s")
        print(f"  Segmentation: {segmentation_time:.2f}s")
        print(f"  Semantic QA: {semantic_qa_time:.2f}s")
        print(f"  Total: {pre_analysis_time + segmentation_time + semantic_qa_time:.2f}s")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestPhase21Integration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nIntegration Test Summary:")
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
