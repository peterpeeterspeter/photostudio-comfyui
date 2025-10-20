"""
Facts Schema Validator for Phase 2.1
Validates Facts V3.1 and V3.2 JSON schemas
"""

import json
import jsonschema
from typing import Dict, List, Any, Optional
from pathlib import Path


class FactsSchemaValidator:
    """
    Validates Facts JSON against V3.1 and V3.2 schemas
    """
    
    def __init__(self):
        self.schemas = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """Load V3.1 and V3.2 schemas from files"""
        try:
            # Load V3.1 schema
            v31_path = Path(__file__).parent / "facts_v3_1_schema.json"
            if v31_path.exists():
                with open(v31_path, 'r') as f:
                    self.schemas["3.1"] = json.load(f)
            
            # Load V3.2 schema
            v32_path = Path(__file__).parent / "facts_v3_2_schema.json"
            if v32_path.exists():
                with open(v32_path, 'r') as f:
                    self.schemas["3.2"] = json.load(f)
                    
        except Exception as e:
            print(f"Warning: Failed to load schemas: {e}")
    
    def validate_facts(self, facts_data: Dict, schema_version: str = "3.2") -> Dict:
        """
        Validate facts data against specified schema version.
        
        Args:
            facts_data: Facts JSON data to validate
            schema_version: Schema version to validate against ("3.1" or "3.2")
            
        Returns:
            Dict with validation results
        """
        if schema_version not in self.schemas:
            return {
                "valid": False,
                "error": f"Schema version {schema_version} not available",
                "available_schemas": list(self.schemas.keys())
            }
        
        try:
            # Get schema
            schema = self.schemas[schema_version]
            
            # Validate against schema
            jsonschema.validate(facts_data, schema)
            
            # Additional custom validations
            custom_validation = self._custom_validation(facts_data, schema_version)
            
            return {
                "valid": True,
                "schema_version": schema_version,
                "custom_validation": custom_validation,
                "message": "Facts data is valid"
            }
            
        except jsonschema.ValidationError as e:
            return {
                "valid": False,
                "error": f"Schema validation failed: {e.message}",
                "path": ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root",
                "schema_version": schema_version
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "schema_version": schema_version
            }
    
    def _custom_validation(self, facts_data: Dict, schema_version: str) -> Dict:
        """Perform custom validations beyond JSON schema"""
        issues = []
        warnings = []
        
        # Check schema version consistency
        if "schema_version" in facts_data:
            if facts_data["schema_version"] != schema_version:
                issues.append(f"Schema version mismatch: expected {schema_version}, got {facts_data['schema_version']}")
        
        # V3.2 specific validations
        if schema_version == "3.2":
            # Check pre_analysis fields
            if "pre_analysis" in facts_data:
                pre_analysis = facts_data["pre_analysis"]
                
                # Validate dominant colors format
                if "dominant_colors" in pre_analysis:
                    for color in pre_analysis["dominant_colors"]:
                        if not self._is_valid_hex_color(color):
                            issues.append(f"Invalid hex color format: {color}")
                
                # Validate pattern complexity
                if "pattern_complexity" in pre_analysis:
                    valid_complexities = ["high", "medium", "low"]
                    if pre_analysis["pattern_complexity"] not in valid_complexities:
                        issues.append(f"Invalid pattern complexity: {pre_analysis['pattern_complexity']}")
                
                # Validate exposure and contrast ranges
                if "exposure" in pre_analysis:
                    exposure = pre_analysis["exposure"]
                    if not (0.0 <= exposure <= 1.0):
                        issues.append(f"Exposure out of range [0.0, 1.0]: {exposure}")
                
                if "contrast" in pre_analysis:
                    contrast = pre_analysis["contrast"]
                    if not (0.0 <= contrast <= 1.0):
                        issues.append(f"Contrast out of range [0.0, 1.0]: {contrast}")
            
            # Check segmentation quality metrics
            if "segmentation" in facts_data:
                segmentation = facts_data["segmentation"]
                
                # Validate mask quality score
                if "mask_quality_score" in segmentation:
                    quality_score = segmentation["mask_quality_score"]
                    if not (0.0 <= quality_score <= 1.0):
                        issues.append(f"Mask quality score out of range [0.0, 1.0]: {quality_score}")
                
                # Validate mask weights sum to 1.0
                if "mask_weights" in segmentation:
                    weights = segmentation["mask_weights"]
                    weight_sum = sum(weights.values())
                    if abs(weight_sum - 1.0) > 0.01:  # Allow small floating point errors
                        warnings.append(f"Mask weights don't sum to 1.0: {weight_sum}")
            
            # Check QA metrics
            if "qa_metrics" in facts_data:
                qa_metrics = facts_data["qa_metrics"]
                
                # Validate QA total score
                if "qa_total" in qa_metrics:
                    qa_total = qa_metrics["qa_total"]
                    if not (0.0 <= qa_total <= 1.0):
                        issues.append(f"QA total score out of range [0.0, 1.0]: {qa_total}")
                
                # Validate weights sum to 1.0
                if "weights" in qa_metrics:
                    weights = qa_metrics["weights"]
                    weight_sum = sum(weights.values())
                    if abs(weight_sum - 1.0) > 0.01:
                        warnings.append(f"QA weights don't sum to 1.0: {weight_sum}")
        
        # General validations for all versions
        # Check garment parts
        if "garment" in facts_data and "parts" in facts_data["garment"]:
            parts = facts_data["garment"]["parts"]
            
            for i, part in enumerate(parts):
                # Validate part color hex
                if "color_hex" in part:
                    if not self._is_valid_hex_color(part["color_hex"]):
                        issues.append(f"Part {i} has invalid hex color: {part['color_hex']}")
                
                # Validate score ranges
                score_fields = ["seam_quality", "sharpness_needed", "transparency", "confidence"]
                for field in score_fields:
                    if field in part:
                        score = part[field]
                        if not (0.0 <= score <= 1.0):
                            issues.append(f"Part {i} {field} out of range [0.0, 1.0]: {score}")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "passed": len(issues) == 0
        }
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """Check if string is a valid hex color"""
        if not isinstance(color, str):
            return False
        
        color = color.lstrip('#')
        if len(color) != 6:
            return False
        
        try:
            int(color, 16)
            return True
        except ValueError:
            return False
    
    def validate_file(self, file_path: str, schema_version: str = "3.2") -> Dict:
        """
        Validate facts JSON file against schema.
        
        Args:
            file_path: Path to facts JSON file
            schema_version: Schema version to validate against
            
        Returns:
            Dict with validation results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                facts_data = json.load(f)
            
            result = self.validate_facts(facts_data, schema_version)
            result["file_path"] = file_path
            
            return result
            
        except FileNotFoundError:
            return {
                "valid": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON: {str(e)}",
                "file_path": file_path
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"File validation error: {str(e)}",
                "file_path": file_path
            }
    
    def batch_validate(self, file_paths: List[str], schema_version: str = "3.2") -> Dict:
        """
        Validate multiple facts files.
        
        Args:
            file_paths: List of paths to facts JSON files
            schema_version: Schema version to validate against
            
        Returns:
            Dict with batch validation results
        """
        results = []
        valid_count = 0
        
        for file_path in file_paths:
            result = self.validate_file(file_path, schema_version)
            results.append(result)
            
            if result.get("valid", False):
                valid_count += 1
        
        return {
            "total_files": len(file_paths),
            "valid_files": valid_count,
            "invalid_files": len(file_paths) - valid_count,
            "pass_rate": (valid_count / len(file_paths)) * 100 if file_paths else 0,
            "results": results,
            "schema_version": schema_version
        }


def main():
    """Command line interface for schema validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Facts JSON schemas')
    parser.add_argument('files', nargs='+', help='Facts JSON files to validate')
    parser.add_argument('--schema-version', default='3.2', choices=['3.1', '3.2'],
                       help='Schema version to validate against')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed validation results')
    
    args = parser.parse_args()
    
    validator = FactsSchemaValidator()
    
    if len(args.files) == 1:
        # Single file validation
        result = validator.validate_file(args.files[0], args.schema_version)
        
        if result["valid"]:
            print(f"✅ {args.files[0]} is valid (schema {args.schema_version})")
            if args.verbose and "custom_validation" in result:
                custom = result["custom_validation"]
                if custom["warnings"]:
                    print("Warnings:")
                    for warning in custom["warnings"]:
                        print(f"  ⚠️  {warning}")
        else:
            print(f"❌ {args.files[0]} is invalid:")
            print(f"   Error: {result['error']}")
            if "path" in result:
                print(f"   Path: {result['path']}")
    else:
        # Batch validation
        result = validator.batch_validate(args.files, args.schema_version)
        
        print(f"Batch Validation Results (Schema {args.schema_version}):")
        print(f"Total files: {result['total_files']}")
        print(f"Valid files: {result['valid_files']}")
        print(f"Invalid files: {result['invalid_files']}")
        print(f"Pass rate: {result['pass_rate']:.1f}%")
        
        if args.verbose:
            print("\nDetailed Results:")
            for file_result in result["results"]:
                status = "✅" if file_result["valid"] else "❌"
                print(f"  {status} {file_result['file_path']}")
                if not file_result["valid"]:
                    print(f"    Error: {file_result['error']}")


if __name__ == "__main__":
    main()
