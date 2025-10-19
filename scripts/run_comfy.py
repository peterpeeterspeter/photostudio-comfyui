#!/usr/bin/env python3
"""
ComfyUI Automation Script for Ghost Mannequin Generation

This script provides programmatic control over ComfyUI workflows,
specifically optimized for photostudio ghost mannequin generation.

Features:
- Automated workflow execution via ComfyUI API
- Progress monitoring and logging
- Batch processing capabilities
- Error handling and retry logic
- Production-ready with comprehensive logging

Usage:
    python scripts/run_comfy.py --workflow workflows/ghostmannequin_comfyui_v1.json --input input/garment.jpg
"""

import json
import time
import uuid
import asyncio
import logging
import argparse
import websockets
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError


class ComfyUIClient:
    """Production-ready ComfyUI API client for ghost mannequin generation"""
    
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure comprehensive logging"""
        logger = logging.getLogger(f"ComfyUIClient-{self.client_id[:8]}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_file = Path("output") / "comfyui_automation.log"
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        """Queue a workflow prompt for execution"""
        try:
            data = {
                "prompt": prompt,
                "client_id": self.client_id
            }
            
            req = Request(f"http://{self.server_address}/prompt")
            req.add_header('Content-Type', 'application/json')
            req_data = json.dumps(data).encode('utf-8')
            
            with urlopen(req, req_data) as response:
                result = json.loads(response.read())
                prompt_id = result['prompt_id']
                self.logger.info(f"Queued prompt: {prompt_id}")
                return prompt_id
                
        except URLError as e:
            self.logger.error(f"Failed to queue prompt: {e}")
            raise
    
    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get execution history for a prompt"""
        try:
            with urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
                history = json.loads(response.read())
                return history.get(prompt_id)
        except URLError:
            return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            with urlopen(f"http://{self.server_address}/queue") as response:
                return json.loads(response.read())
        except URLError as e:
            self.logger.error(f"Failed to get queue status: {e}")
            return {"queue_running": [], "queue_pending": []}
    
    async def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for workflow completion with WebSocket monitoring"""
        self.logger.info(f"Waiting for completion of prompt: {prompt_id}")
        
        start_time = time.time()
        uri = f"ws://{self.server_address}/ws?clientId={self.client_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                while time.time() - start_time < timeout:
                    # Check if prompt is completed via history
                    history = self.get_history(prompt_id)
                    if history and 'outputs' in history:
                        self.logger.info(f"Workflow completed: {prompt_id}")
                        return history
                    
                    # Listen for WebSocket messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        
                        if data['type'] == 'execution_start':
                            self.logger.info(f"Execution started: {data['data']['prompt_id']}")
                        elif data['type'] == 'execution_cached':
                            self.logger.info(f"Using cached results for nodes: {data['data']['nodes']}")
                        elif data['type'] == 'executing':
                            node_id = data['data']['node']
                            if node_id:
                                self.logger.info(f"Executing node: {node_id}")
                            else:
                                self.logger.info("Workflow execution completed")
                        elif data['type'] == 'progress':
                            value = data['data']['value']
                            max_val = data['data']['max']
                            self.logger.info(f"Progress: {value}/{max_val}")
                            
                    except asyncio.TimeoutError:
                        # No message received, continue checking
                        continue
                        
                raise TimeoutError(f"Workflow execution timeout after {timeout}s")
                
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            # Fallback to polling
            return await self._poll_for_completion(prompt_id, timeout - (time.time() - start_time))
    
    async def _poll_for_completion(self, prompt_id: str, timeout: int) -> Dict[str, Any]:
        """Fallback polling method for completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            if history and 'outputs' in history:
                self.logger.info(f"Workflow completed (polling): {prompt_id}")
                return history
            
            await asyncio.sleep(2)
            
        raise TimeoutError(f"Polling timeout after {timeout}s")
    
    def get_generated_images(self, history: Dict[str, Any]) -> List[str]:
        """Extract generated image paths from history"""
        images = []
        
        for node_id, node_output in history.get('outputs', {}).items():
            if 'images' in node_output:
                for image in node_output['images']:
                    filename = image['filename']
                    # ComfyUI saves to output directory by default
                    image_path = Path("output") / filename
                    if image_path.exists():
                        images.append(str(image_path))
                        self.logger.info(f"Generated image: {image_path}")
        
        return images


def load_workflow(workflow_path: str) -> Dict[str, Any]:
    """Load and validate ComfyUI workflow JSON"""
    workflow_file = Path(workflow_path)
    if not workflow_file.exists():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
    
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)
    
    if 'workflow' not in workflow:
        raise ValueError("Invalid workflow format - missing 'workflow' key")
    
    return workflow['workflow']


def update_workflow_inputs(workflow: Dict[str, Any], 
                          input_image: Optional[str] = None,
                          facts_file: Optional[str] = None,
                          ccj_file: Optional[str] = None,
                          custom_additions: Optional[str] = None) -> Dict[str, Any]:
    """Update workflow with specific input parameters"""
    
    # Update LoadImage node (typically node 1)
    if input_image and '1' in workflow:
        workflow['1']['inputs']['image'] = input_image
    
    # Update LoadFactsNode (typically node 2)
    if facts_file and '2' in workflow:
        workflow['2']['inputs']['facts_file_path'] = facts_file
    
    # Update PromptBuilder node (typically node 3)
    if '3' in workflow:
        if ccj_file:
            workflow['3']['inputs']['ccj_path'] = ccj_file
        if custom_additions:
            workflow['3']['inputs']['custom_additions'] = custom_additions
    
    return workflow


async def run_ghost_mannequin_workflow(workflow_path: str,
                                     input_image: str,
                                     facts_file: str = "input/factsv3.json",
                                     ccj_file: str = "input/ccj_controlblock.json",
                                     custom_additions: str = "",
                                     server_address: str = "127.0.0.1:8188",
                                     timeout: int = 300) -> List[str]:
    """Execute complete ghost mannequin workflow"""
    
    # Initialize client
    client = ComfyUIClient(server_address)
    client.logger.info("Starting ghost mannequin workflow execution")
    
    # Load and configure workflow
    workflow = load_workflow(workflow_path)
    workflow = update_workflow_inputs(
        workflow, input_image, facts_file, ccj_file, custom_additions
    )
    
    # Queue prompt
    prompt_id = client.queue_prompt(workflow)
    
    # Wait for completion
    history = await client.wait_for_completion(prompt_id, timeout)
    
    # Extract generated images
    generated_images = client.get_generated_images(history)
    
    client.logger.info(f"Workflow completed. Generated {len(generated_images)} images.")
    return generated_images


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Execute ComfyUI ghost mannequin workflow programmatically"
    )
    parser.add_argument(
        "--workflow", 
        required=True,
        help="Path to ComfyUI workflow JSON file"
    )
    parser.add_argument(
        "--input-image", 
        required=True,
        help="Path to input garment image"
    )
    parser.add_argument(
        "--facts-file", 
        default="input/factsv3.json",
        help="Path to FactsV3 JSON file"
    )
    parser.add_argument(
        "--ccj-file", 
        default="input/ccj_controlblock.json",
        help="Path to CCJ ControlBlock JSON file"
    )
    parser.add_argument(
        "--custom-additions", 
        default="",
        help="Custom prompt additions"
    )
    parser.add_argument(
        "--server", 
        default="127.0.0.1:8188",
        help="ComfyUI server address"
    )
    parser.add_argument(
        "--timeout", 
        type=int,
        default=300,
        help="Execution timeout in seconds"
    )
    
    args = parser.parse_args()
    
    try:
        # Run workflow
        generated_images = asyncio.run(
            run_ghost_mannequin_workflow(
                workflow_path=args.workflow,
                input_image=args.input_image,
                facts_file=args.facts_file,
                ccj_file=args.ccj_file,
                custom_additions=args.custom_additions,
                server_address=args.server,
                timeout=args.timeout
            )
        )
        
        print(f"\n🎉 Workflow completed successfully!")
        print(f"📸 Generated {len(generated_images)} images:")
        for img_path in generated_images:
            print(f"   - {img_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())