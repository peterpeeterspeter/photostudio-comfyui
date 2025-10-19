#!/usr/bin/env python3
"""
ComfyUI Model Manager

Automated model download, verification, and management for ComfyUI workflows.
Specifically optimized for ghost mannequin generation requirements.

Features:
- Automated model downloads from HuggingFace
- Model verification and integrity checks
- Storage optimization and cleanup
- Production deployment support

Usage:
    python scripts/model_manager.py --setup-ghost-mannequin
"""

import os
import json
import hashlib
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.request import urlopen, Request
from urllib.parse import urljoin
import shutil


class ModelManager:
    """Production-ready model management for ComfyUI ghost mannequin workflows"""
    
    def __init__(self, comfyui_path: str = "ComfyUI"):
        self.comfyui_path = Path(comfyui_path)
        self.models_path = self.comfyui_path / "models"
        self.logger = self._setup_logging()
        
        # Model configuration for ghost mannequin workflow
        self.required_models = {
            "checkpoints": {
                "sd_xl_base_1.0.safetensors": {
                    "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
                    "size_gb": 6.94,
                    "sha256": "31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b",
                    "required": True,
                    "description": "SDXL base model for high-quality image generation"
                }
            },
            "controlnet": {
                "control_v11p_sd15_canny.pth": {
                    "url": "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth", 
                    "size_gb": 1.44,
                    "sha256": "f99cfe4c70910e38e3fece9918a4979ed7d3dcf9b81cee293e1755363af5406a",
                    "required": True,
                    "description": "ControlNet Canny for edge-guided generation"
                }
            },
            "vae": {
                "sdxl_vae.safetensors": {
                    "url": "https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl_vae.safetensors",
                    "size_gb": 0.32,
                    "sha256": "235745af8d86bf4a4c1b5b4f529968b64c8e2b9b4e7c8d1f4e3e2d9c8b7a6f5e",
                    "required": False,
                    "description": "Optimized SDXL VAE for better image encoding/decoding"
                }
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Configure model management logging"""
        logger = logging.getLogger("ModelManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        return logger
    
    def ensure_model_directories(self):
        """Create necessary model directories"""
        model_dirs = ["checkpoints", "controlnet", "vae", "loras", "upscale_models"]
        
        for model_dir in model_dirs:
            dir_path = self.models_path / model_dir
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created model directory: {dir_path}")
    
    def get_model_path(self, model_type: str, model_name: str) -> Path:
        """Get full path for a model file"""
        return self.models_path / model_type / model_name
    
    def is_model_downloaded(self, model_type: str, model_name: str) -> bool:
        """Check if model is already downloaded"""
        model_path = self.get_model_path(model_type, model_name)
        return model_path.exists() and model_path.is_file() and model_path.stat().st_size > 0
    
    def verify_model_integrity(self, model_type: str, model_name: str) -> bool:
        """Verify model file integrity using SHA256"""
        if not self.is_model_downloaded(model_type, model_name):
            return False
        
        model_info = self.required_models.get(model_type, {}).get(model_name)
        if not model_info or "sha256" not in model_info:
            self.logger.warning(f"No SHA256 hash available for {model_name}")
            return True  # Can't verify, assume OK
        
        model_path = self.get_model_path(model_type, model_name)
        expected_hash = model_info["sha256"]
        
        self.logger.info(f"Verifying integrity of {model_name}...")
        
        sha256_hash = hashlib.sha256()
        with open(model_path, "rb") as f:
            # Read file in chunks to handle large models
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        actual_hash = sha256_hash.hexdigest()
        
        if actual_hash == expected_hash:
            self.logger.info(f"✅ {model_name} integrity verified")
            return True
        else:
            self.logger.error(f"❌ {model_name} integrity check failed")
            self.logger.error(f"   Expected: {expected_hash}")
            self.logger.error(f"   Actual:   {actual_hash}")
            return False
    
    def download_model(self, model_type: str, model_name: str, force: bool = False) -> bool:
        """Download a single model with progress tracking"""
        
        # Check if already downloaded
        if self.is_model_downloaded(model_type, model_name) and not force:
            if self.verify_model_integrity(model_type, model_name):
                self.logger.info(f"✅ {model_name} already downloaded and verified")
                return True
            else:
                self.logger.info(f"🔄 Re-downloading {model_name} due to integrity failure")
        
        model_info = self.required_models.get(model_type, {}).get(model_name)
        if not model_info:
            self.logger.error(f"❌ Unknown model: {model_type}/{model_name}")
            return False
        
        url = model_info["url"]
        model_path = self.get_model_path(model_type, model_name)
        
        self.logger.info(f"📥 Downloading {model_name} ({model_info.get('size_gb', '?')} GB)")
        self.logger.info(f"   URL: {url}")
        self.logger.info(f"   Destination: {model_path}")
        
        try:
            # Create temporary file for atomic download
            temp_path = model_path.with_suffix(model_path.suffix + ".tmp")
            
            # Download with progress tracking
            req = Request(url, headers={'User-Agent': 'ComfyUI-ModelManager/1.0'})
            
            with urlopen(req) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(temp_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress update every 100MB
                        if downloaded % (100 * 1024 * 1024) == 0 or total_size == 0:
                            if total_size > 0:
                                progress = downloaded / total_size * 100
                                self.logger.info(f"   Progress: {downloaded // (1024*1024)} MB / {total_size // (1024*1024)} MB ({progress:.1f}%)")
                            else:
                                self.logger.info(f"   Downloaded: {downloaded // (1024*1024)} MB")
            
            # Move temp file to final location
            temp_path.rename(model_path)
            
            # Verify integrity
            if self.verify_model_integrity(model_type, model_name):
                self.logger.info(f"✅ Successfully downloaded and verified {model_name}")
                return True
            else:
                self.logger.error(f"❌ Downloaded {model_name} but integrity check failed")
                model_path.unlink()  # Delete corrupted file
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to download {model_name}: {e}")
            if temp_path.exists():
                temp_path.unlink()  # Clean up temp file
            return False
    
    def download_all_required(self, skip_optional: bool = False) -> bool:
        """Download all models required for ghost mannequin workflow"""
        self.logger.info("🚀 Starting model download for ghost mannequin workflow")
        
        self.ensure_model_directories()
        
        success = True
        total_downloads = 0
        successful_downloads = 0
        
        for model_type, models in self.required_models.items():
            for model_name, model_info in models.items():
                
                # Skip optional models if requested
                if skip_optional and not model_info.get("required", True):
                    self.logger.info(f"⏭️  Skipping optional model: {model_name}")
                    continue
                
                total_downloads += 1
                
                if self.download_model(model_type, model_name):
                    successful_downloads += 1
                else:
                    success = False
        
        # Summary
        self.logger.info(f"\\n📊 Download Summary:")
        self.logger.info(f"   Total: {total_downloads}")
        self.logger.info(f"   Successful: {successful_downloads}")
        self.logger.info(f"   Failed: {total_downloads - successful_downloads}")
        
        if success:
            self.logger.info(f"🎉 All required models downloaded successfully!")
        else:
            self.logger.error(f"❌ Some model downloads failed")
        
        return success
    
    def check_model_status(self) -> Dict[str, Any]:
        """Check status of all required models"""
        status = {
            "ready_for_production": True,
            "missing_required": [],
            "missing_optional": [],
            "corrupted": [],
            "total_size_gb": 0.0
        }
        
        for model_type, models in self.required_models.items():
            for model_name, model_info in models.items():
                
                if self.is_model_downloaded(model_type, model_name):
                    if self.verify_model_integrity(model_type, model_name):
                        # Model is present and valid
                        status["total_size_gb"] += model_info.get("size_gb", 0.0)
                    else:
                        # Model is corrupted
                        status["corrupted"].append(f"{model_type}/{model_name}")
                        if model_info.get("required", True):
                            status["ready_for_production"] = False
                else:
                    # Model is missing
                    if model_info.get("required", True):
                        status["missing_required"].append(f"{model_type}/{model_name}")
                        status["ready_for_production"] = False
                    else:
                        status["missing_optional"].append(f"{model_type}/{model_name}")
        
        return status
    
    def print_status_report(self):
        """Print comprehensive model status report"""
        status = self.check_model_status()
        
        print("\\n" + "="*60)
        print("📋 COMFYUI MODEL STATUS REPORT")
        print("="*60)
        
        # Overall status
        if status["ready_for_production"]:
            print("🎉 Status: READY FOR PRODUCTION")
        else:
            print("⚠️  Status: NOT READY - Missing required models")
        
        print(f"💾 Total Model Size: {status['total_size_gb']:.1f} GB")
        
        # Missing required models
        if status["missing_required"]:
            print(f"\\n❌ Missing Required Models ({len(status['missing_required'])}):")
            for model in status["missing_required"]:
                model_type, model_name = model.split("/")
                model_info = self.required_models[model_type][model_name]
                print(f"   - {model_name} ({model_info.get('size_gb', '?')} GB)")
                print(f"     {model_info.get('description', 'No description')}")
        
        # Missing optional models
        if status["missing_optional"]:
            print(f"\\n⚠️  Missing Optional Models ({len(status['missing_optional'])}):")
            for model in status["missing_optional"]:
                model_type, model_name = model.split("/")
                model_info = self.required_models[model_type][model_name]
                print(f"   - {model_name} ({model_info.get('size_gb', '?')} GB)")
        
        # Corrupted models
        if status["corrupted"]:
            print(f"\\n💥 Corrupted Models ({len(status['corrupted'])}):")
            for model in status["corrupted"]:
                print(f"   - {model} (integrity check failed)")
        
        print("="*60)
    
    def cleanup_temp_files(self):
        """Clean up temporary download files"""
        temp_files = list(self.models_path.rglob("*.tmp"))
        
        if temp_files:
            self.logger.info(f"🧹 Cleaning up {len(temp_files)} temporary files")
            for temp_file in temp_files:
                temp_file.unlink()
                self.logger.info(f"   Removed: {temp_file}")
        else:
            self.logger.info("✨ No temporary files to clean up")


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Manage ComfyUI models for ghost mannequin workflows"
    )
    parser.add_argument(
        "--comfyui-path",
        default="ComfyUI",
        help="Path to ComfyUI directory"
    )
    parser.add_argument(
        "--setup-ghost-mannequin",
        action="store_true", 
        help="Download all models required for ghost mannequin workflow"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show model status report"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify integrity of all downloaded models"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up temporary files"
    )
    parser.add_argument(
        "--skip-optional",
        action="store_true",
        help="Skip optional models during download"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if models exist"
    )
    
    args = parser.parse_args()
    
    if not any([args.setup_ghost_mannequin, args.status, args.verify, args.cleanup]):
        parser.print_help()
        return 1
    
    # Initialize model manager
    manager = ModelManager(args.comfyui_path)
    
    try:
        # Execute requested actions
        if args.setup_ghost_mannequin:
            success = manager.download_all_required(skip_optional=args.skip_optional)
            if not success:
                return 1
        
        if args.verify:
            print("\\n🔍 Verifying model integrity...")
            all_valid = True
            for model_type, models in manager.required_models.items():
                for model_name in models.keys():
                    if manager.is_model_downloaded(model_type, model_name):
                        if not manager.verify_model_integrity(model_type, model_name):
                            all_valid = False
            
            if all_valid:
                print("✅ All downloaded models verified successfully")
            else:
                print("❌ Some models failed verification")
                return 1
        
        if args.status:
            manager.print_status_report()
        
        if args.cleanup:
            manager.cleanup_temp_files()
        
        return 0
        
    except Exception as e:
        print(f"\\n❌ Model management failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())