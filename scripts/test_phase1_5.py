"""
Phase 1.5 Test Suite
Comprehensive testing for ghost mannequin pipeline components
"""

import os
import json
import sys
import unittest
from pathlib import Path
from typing import Dict, List
import numpy as np
from PIL import Image
import torch


class TestPhase1_5Components(unittest.TestCase):
    """Test suite for Phase 1.5 components"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.test_data_dir = self.project_root / "input"
        self.output_dir = self.project_root / "output"
        self.workflows_dir = self.project_root / "workflows"
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
    
    def test_rmbg_node_import(self):
        """Test RMBG node can be imported"""
        try:
            sys.path.append(str(self.project_root / "ComfyUI" / "custom_nodes" / "comfyui_rmbg"))
            from rmbg_node import RMBGNode
            self.assertTrue(True, "RMBG node imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import RMBG node: {e}")
    
    def test_light_facts_schema(self):
        """Test Light Facts schema structure"""
        schema_path = self.test_data_dir / "light_facts_schema.json"
        self.assertTrue(schema_path.exists(), "Light Facts schema file exists")
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Check required fields
        self.assertIn("analysis_mode", schema)
        self.assertIn("garment", schema)
        self.assertIn("photography", schema)
        self.assertIn("routing", schema)
        
        # Check garment structure
        garment = schema["garment"]
        required_garment_fields = [
            "category", "silhouette", "fabric", "finish",
            "color_hex", "color_name", "closures", "pockets_count"
        ]
        for field in required_garment_fields:
            self.assertIn(field, garment, f"Missing garment field: {field}")
    
    def test_quality_gates_import(self):
        """Test quality gate nodes can be imported"""
        try:
            sys.path.append(str(self.project_root / "ComfyUI" / "custom_nodes" / "quality_gates"))
            from edge_gate import QualityGateEdge
            from bg_gate import QualityGateBackground
            self.assertTrue(True, "Quality gate nodes imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import quality gate nodes: {e}")
    
    def test_workflow_files_exist(self):
        """Test that workflow files exist and are valid JSON"""
        workflow_files = [
            "phase1_5_mvp.json",
            "phase1_5_complete.json"
        ]
        
        for workflow_file in workflow_files:
            workflow_path = self.workflows_dir / workflow_file
            self.assertTrue(workflow_path.exists(), f"Workflow file exists: {workflow_file}")
            
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
            
            self.assertIn("nodes", workflow, f"Workflow has nodes: {workflow_file}")
            self.assertIn("last_node_id", workflow, f"Workflow has last_node_id: {workflow_file}")
    
    def test_config_file_structure(self):
        """Test configuration file structure"""
        config_path = self.project_root / "config" / "phase1_5_params.yaml"
        self.assertTrue(config_path.exists(), "Configuration file exists")
        
        # Basic file structure check (would need PyYAML for full validation)
        with open(config_path, 'r') as f:
            content = f.read()
        
        required_sections = [
            "segmentation:", "generation:", "quality_thresholds:",
            "inpaint:", "prompting:", "routing:"
        ]
        
        for section in required_sections:
            self.assertIn(section, content, f"Config contains section: {section}")
    
    def test_batch_processor_import(self):
        """Test batch processor can be imported"""
        try:
            sys.path.append(str(self.project_root / "scripts"))
            from batch_ghost_processor import BatchGhostProcessor
            self.assertTrue(True, "Batch processor imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import batch processor: {e}")
    
    def test_quality_validator_import(self):
        """Test quality validator can be imported"""
        try:
            sys.path.append(str(self.project_root / "scripts"))
            from quality_validator import QualityValidator
            self.assertTrue(True, "Quality validator imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import quality validator: {e}")


class TestPhase1_5Integration(unittest.TestCase):
    """Integration tests for Phase 1.5 pipeline"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.project_root = Path(__file__).parent.parent
        self.test_data_dir = self.project_root / "input"
        self.output_dir = self.project_root / "output"
    
    def test_light_facts_prompt_generation(self):
        """Test Light Facts prompt generation"""
        try:
            sys.path.append(str(self.project_root / "ComfyUI" / "custom_nodes"))
            from light_facts_prompt import PromptFromLightFacts
            
            # Create test facts
            test_facts = {
                "analysis_mode": "light",
                "garment": {
                    "category": "test shirt",
                    "silhouette": "tailored",
                    "fabric": "cotton",
                    "finish": "matte",
                    "color_hex": "#000000",
                    "color_name": "black",
                    "closures": "buttons",
                    "pockets_count": 1
                },
                "photography": {
                    "bg": "pure_white",
                    "lighting": "soft_even_high_key"
                }
            }
            
            prompt_builder = PromptFromLightFacts()
            positive, negative, constraints = prompt_builder.build_prompts(
                json.dumps(test_facts),
                "detailed",
                True
            )
            
            self.assertIsInstance(positive, str)
            self.assertIsInstance(negative, str)
            self.assertIsInstance(constraints, str)
            self.assertIn("test shirt", positive)
            self.assertIn("#000000", positive)
            
        except ImportError as e:
            self.skipTest(f"Light Facts prompt node not available: {e}")
    
    def test_model_router_logic(self):
        """Test model router decision logic"""
        try:
            sys.path.append(str(self.project_root / "ComfyUI" / "custom_nodes"))
            from model_router import ModelRouter
            
            router = ModelRouter()
            
            # Test SDXL selection for simple fabric
            simple_facts = {
                "garment": {
                    "fabric": "cotton",
                    "finish": "matte",
                    "category": "shirt"
                },
                "routing": {"suggested_model": "sdxl"}
            }
            
            model_choice, reason = router._analyze_garment_requirements(
                simple_facts["garment"], "sdxl"
            )
            
            self.assertEqual(model_choice, "sdxl")
            self.assertIn("SDXL", reason)
            
        except ImportError as e:
            self.skipTest(f"Model router not available: {e}")
    
    def test_quality_gate_thresholds(self):
        """Test quality gate threshold validation"""
        try:
            sys.path.append(str(self.project_root / "ComfyUI" / "custom_nodes" / "quality_gates"))
            from edge_gate import QualityGateEdge
            from bg_gate import QualityGateBackground
            
            # Test edge gate
            edge_gate = QualityGateEdge()
            self.assertEqual(edge_gate.INPUT_TYPES()["required"]["ssim_threshold"]["default"], 0.75)
            self.assertEqual(edge_gate.INPUT_TYPES()["required"]["alpha_threshold"]["default"], 0.97)
            
            # Test background gate
            bg_gate = QualityGateBackground()
            self.assertEqual(bg_gate.INPUT_TYPES()["required"]["purity_threshold"]["default"], 0.95)
            self.assertEqual(bg_gate.INPUT_TYPES()["required"]["white_threshold"]["default"], 250.0)
            
        except ImportError as e:
            self.skipTest(f"Quality gates not available: {e}")


class TestPhase1_5Performance(unittest.TestCase):
    """Performance tests for Phase 1.5 components"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.project_root = Path(__file__).parent.parent
    
    def test_mask_processing_performance(self):
        """Test mask processing utility performance"""
        try:
            sys.path.append(str(self.project_root / "ComfyUI" / "custom_nodes"))
            from mask_utils_node import MaskDilation, MaskToAlphaBorder, MaskStats
            
            # Create test mask
            test_mask = torch.ones((1, 512, 512), dtype=torch.float32)
            
            # Test dilation
            dilation_node = MaskDilation()
            start_time = time.time()
            processed_mask, area_ratio = dilation_node.process_mask(test_mask, 8, 3, "dilate")
            dilation_time = time.time() - start_time
            
            self.assertLess(dilation_time, 1.0, "Mask dilation should complete in < 1 second")
            self.assertIsInstance(processed_mask, torch.Tensor)
            self.assertIsInstance(area_ratio, float)
            
        except ImportError as e:
            self.skipTest(f"Mask utilities not available: {e}")
        except NameError:
            # time module not imported
            import time
            self.test_mask_processing_performance()


def run_test_cases():
    """Run all test cases and generate report"""
    print("Running Phase 1.5 Test Suite...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPhase1_5Components))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase1_5Integration))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase1_5Performance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Overall result
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall Result: {'PASS' if success else 'FAIL'}")
    
    return success


def create_test_data():
    """Create test data for validation"""
    project_root = Path(__file__).parent.parent
    test_data_dir = project_root / "input"
    
    # Create test Light Facts
    test_facts = {
        "schema_version": "3.1",
        "analysis_mode": "light",
        "garment": {
            "category": "oxford dress shirt",
            "silhouette": "tailored",
            "fabric": "mid-weight cotton twill",
            "finish": "matte",
            "color_hex": "#1a237e",
            "color_name": "navy blue",
            "closures": "front button placket",
            "pockets_count": 1,
            "label_text": "Test Brand ©",
            "special_notes": "test garment for validation"
        },
        "photography": {
            "bg": "pure_white",
            "lighting": "soft_even_high_key",
            "frame": "4:5",
            "coverage_pct": 85
        },
        "routing": {
            "suggested_model": "sdxl"
        }
    }
    
    # Save test facts
    test_facts_path = test_data_dir / "test_light_facts.json"
    with open(test_facts_path, 'w') as f:
        json.dump(test_facts, f, indent=2)
    
    print(f"Created test data: {test_facts_path}")


if __name__ == "__main__":
    import time
    
    # Create test data
    create_test_data()
    
    # Run tests
    success = run_test_cases()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
