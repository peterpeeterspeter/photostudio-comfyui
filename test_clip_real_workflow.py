#!/usr/bin/env python3
"""
Real CLIP Workflow Test
Test if CLIP models actually work in ComfyUI workflows
"""

import requests
import json
import time
import os

def test_real_clip_workflow():
    """Test CLIP models with a real SDXL workflow"""
    
    print("🧪 Real CLIP Workflow Test")
    print("=" * 40)
    
    # Check if ComfyUI is running
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        if response.status_code == 200:
            print("✅ ComfyUI is running")
        else:
            print("❌ ComfyUI not responding")
            return False
    except Exception as e:
        print(f"❌ ComfyUI not running: {e}")
        return False
    
    # Create a real SDXL workflow with CLIP
    workflow = {
        "1": {
            "inputs": {
                "image": "test_garment.jpg",
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {
                "title": "Load Image"
            }
        },
        "2": {
            "inputs": {
                "text": "a beautiful garment, high quality, professional photography, ghost mannequin effect",
                "clip": ["3", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "3": {
            "inputs": {
                "clip_name": "clip_l.safetensors",
                "type": "stable_diffusion"
            },
            "class_type": "CLIPLoader",
            "_meta": {
                "title": "CLIP Loader"
            }
        },
        "4": {
            "inputs": {
                "text": "low quality, blurry, distorted, person, human, mannequin visible",
                "clip": ["3", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Negative)"
            }
        },
        "5": {
            "inputs": {
                "ckpt_name": "sd_xl_base_1.0.safetensors"
            },
            "class_type": "CheckpointLoaderSimple",
            "_meta": {
                "title": "Load Checkpoint"
            }
        },
        "6": {
            "inputs": {
                "text": "a beautiful garment, high quality, professional photography, ghost mannequin effect",
                "clip": ["5", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "7": {
            "inputs": {
                "text": "low quality, blurry, distorted, person, human, mannequin visible",
                "clip": ["5", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Negative)"
            }
        },
        "8": {
            "inputs": {
                "seed": 42,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["5", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["9", 0]
            },
            "class_type": "KSampler",
            "_meta": {
                "title": "KSampler"
            }
        },
        "9": {
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage",
            "_meta": {
                "title": "Empty Latent Image"
            }
        },
        "10": {
            "inputs": {
                "samples": ["8", 0],
                "vae": ["5", 2]
            },
            "class_type": "VAEDecode",
            "_meta": {
                "title": "VAE Decode"
            }
        },
        "11": {
            "inputs": {
                "filename_prefix": "real_clip_test",
                "images": ["10", 0]
            },
            "class_type": "SaveImage",
            "_meta": {
                "title": "Save Image"
            }
        }
    }
    
    print(f"✅ Created workflow with {len(workflow)} nodes")
    
    # Check if test image exists
    test_image = "input/test_garment.jpg"
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return False
    
    print(f"✅ Found: {test_image}")
    
    # Queue the workflow
    try:
        print("📤 Queuing real CLIP workflow...")
        response = requests.post("http://127.0.0.1:8188/prompt", 
                               json={"prompt": workflow}, 
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get("prompt_id")
            print(f"✅ Workflow queued with ID: {prompt_id}")
            
            # Monitor execution
            print("⏳ Monitoring execution...")
            start_time = time.time()
            
            while time.time() - start_time < 120:  # 2 minute timeout
                try:
                    response = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=5)
                    if response.status_code == 200:
                        history = response.json()
                        if prompt_id in history:
                            status = history[prompt_id].get("status", {})
                            if status.get("status_str") == "success":
                                print("✅ Real CLIP workflow completed successfully!")
                                return True
                            elif status.get("status_str") == "error":
                                print(f"❌ Real CLIP workflow failed: {status.get('message', 'Unknown error')}")
                                return False
                    
                    time.sleep(3)
                except Exception as e:
                    print(f"⚠️  Request error: {e}")
                    time.sleep(3)
            
            print("⏰ Timeout after 120 seconds")
            return False
            
        else:
            print(f"❌ Failed to queue workflow: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_real_clip_workflow()
    if success:
        print("\n🎉 CLIP models are working in real SDXL workflows!")
    else:
        print("\n❌ Real CLIP workflow test failed!")
        print("🔧 Check ComfyUI logs for details")
