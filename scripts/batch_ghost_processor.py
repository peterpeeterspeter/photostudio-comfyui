"""
Batch Ghost Mannequin Processor
Automated batch processing with ComfyUI API integration
"""

import os
import json
import time
import requests
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading
import queue
from pathlib import Path


class BatchGhostProcessor:
    """
    Batch processor for ghost mannequin generation
    Integrates with ComfyUI API for automated processing
    """
    
    def __init__(self, comfyui_url: str = "http://localhost:8188"):
        """Initialize processor with ComfyUI connection"""
        self.comfyui_url = comfyui_url
        self.session = requests.Session()
        self.processing_queue = queue.Queue()
        self.results = []
        self.running = False
        
    def load_workflow(self, workflow_path: str) -> Dict:
        """Load workflow JSON from file"""
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load workflow: {str(e)}")
    
    def prepare_batch(self, input_dir: str, facts_dir: str, output_dir: str) -> List[Dict]:
        """Prepare batch processing tasks"""
        tasks = []
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all image files
        image_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        image_files = []
        
        for file in os.listdir(input_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(file)
        
        # Create tasks for each image
        for image_file in image_files:
            base_name = os.path.splitext(image_file)[0]
            
            # Find corresponding facts file
            facts_file = os.path.join(facts_dir, f"{base_name}.json")
            if not os.path.exists(facts_file):
                facts_file = os.path.join(facts_dir, f"{base_name}_facts.json")
            
            if not os.path.exists(facts_file):
                print(f"Warning: No facts file found for {image_file}")
                continue
            
            task = {
                "image_file": image_file,
                "facts_file": facts_file,
                "base_name": base_name,
                "input_path": os.path.join(input_dir, image_file),
                "facts_path": facts_file,
                "output_path": os.path.join(output_dir, f"ghost_{base_name}.png")
            }
            
            tasks.append(task)
        
        return tasks
    
    def queue_workflow(self, workflow: Dict, task: Dict) -> str:
        """Queue a workflow for processing"""
        try:
            # Modify workflow for this specific task
            modified_workflow = self._modify_workflow_for_task(workflow, task)
            
            # Queue the workflow
            response = self.session.post(
                f"{self.comfyui_url}/prompt",
                json={"prompt": modified_workflow}
            )
            
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")
                print(f"Queued task {task['base_name']} with prompt ID: {prompt_id}")
                return prompt_id
            else:
                raise Exception(f"Failed to queue workflow: {response.text}")
                
        except Exception as e:
            print(f"Error queueing task {task['base_name']}: {str(e)}")
            return None
    
    def _modify_workflow_for_task(self, workflow: Dict, task: Dict) -> Dict:
        """Modify workflow for specific task"""
        modified = workflow.copy()
        
        # Update image input
        if "1" in modified["nodes"]:
            modified["nodes"]["1"]["inputs"]["image"] = task["image_file"]
        
        # Update facts file path
        if "2" in modified["nodes"]:
            modified["nodes"]["2"]["inputs"]["facts_file_path"] = task["facts_path"]
        
        # Update output filename
        if "20" in modified["nodes"]:
            modified["nodes"]["20"]["inputs"]["filename_prefix"] = f"ghost_{task['base_name']}_"
        
        return modified
    
    def monitor_queue(self) -> List[Dict]:
        """Monitor ComfyUI queue and collect results"""
        results = []
        
        try:
            # Get queue status
            response = self.session.get(f"{self.comfyui_url}/queue")
            if response.status_code == 200:
                queue_data = response.json()
                
                # Process completed items
                for item in queue_data.get("queue_running", []):
                    if item.get("status") == "success":
                        results.append({
                            "prompt_id": item.get("prompt_id"),
                            "status": "completed",
                            "timestamp": datetime.now().isoformat()
                        })
                
                for item in queue_data.get("queue_pending", []):
                    results.append({
                        "prompt_id": item.get("prompt_id"),
                        "status": "pending",
                        "timestamp": datetime.now().isoformat()
                    })
        
        except Exception as e:
            print(f"Error monitoring queue: {str(e)}")
        
        return results
    
    def get_history(self, prompt_id: str) -> Optional[Dict]:
        """Get processing history for a prompt ID"""
        try:
            response = self.session.get(f"{self.comfyui_url}/history/{prompt_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting history for {prompt_id}: {str(e)}")
        
        return None
    
    def process_batch(
        self, 
        workflow_path: str, 
        input_dir: str, 
        facts_dir: str, 
        output_dir: str,
        max_concurrent: int = 2
    ) -> Dict:
        """Process entire batch with monitoring"""
        
        print(f"Starting batch processing...")
        print(f"Input directory: {input_dir}")
        print(f"Facts directory: {facts_dir}")
        print(f"Output directory: {output_dir}")
        
        # Load workflow
        workflow = self.load_workflow(workflow_path)
        
        # Prepare tasks
        tasks = self.prepare_batch(input_dir, facts_dir, output_dir)
        print(f"Found {len(tasks)} tasks to process")
        
        # Queue all tasks
        queued_tasks = {}
        for task in tasks:
            prompt_id = self.queue_workflow(workflow, task)
            if prompt_id:
                queued_tasks[prompt_id] = task
        
        print(f"Queued {len(queued_tasks)} tasks")
        
        # Monitor progress
        completed_tasks = []
        failed_tasks = []
        start_time = time.time()
        
        while len(completed_tasks) + len(failed_tasks) < len(queued_tasks):
            # Check queue status
            queue_status = self.monitor_queue()
            
            # Check for completed tasks
            for prompt_id, task in queued_tasks.items():
                if prompt_id in [t["prompt_id"] for t in completed_tasks]:
                    continue
                
                history = self.get_history(prompt_id)
                if history and prompt_id in history:
                    task_info = history[prompt_id]
                    if task_info.get("status", {}).get("status") == "success":
                        completed_tasks.append({
                            "prompt_id": prompt_id,
                            "task": task,
                            "status": "completed",
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"Completed: {task['base_name']}")
                    elif task_info.get("status", {}).get("status") == "error":
                        failed_tasks.append({
                            "prompt_id": prompt_id,
                            "task": task,
                            "status": "failed",
                            "error": task_info.get("status", {}).get("message", "Unknown error"),
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"Failed: {task['base_name']} - {task_info.get('status', {}).get('message', 'Unknown error')}")
            
            # Wait before next check
            time.sleep(5)
        
        # Generate summary
        processing_time = time.time() - start_time
        
        summary = {
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "completed": completed_tasks,
            "failed": failed_tasks
        }
        
        return summary
    
    def run_quality_validation(self, output_dir: str, facts_dir: str) -> Dict:
        """Run quality validation on outputs"""
        try:
            # Import quality validator
            from quality_validator import QualityValidator
            
            validator = QualityValidator()
            report = validator.validate_batch(output_dir, facts_dir)
            
            return report
            
        except Exception as e:
            return {
                "error": f"Failed to run quality validation: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Command line interface for batch processor"""
    parser = argparse.ArgumentParser(description='Batch process ghost mannequin images')
    parser.add_argument('--workflow', required=True, help='Path to workflow JSON file')
    parser.add_argument('--input-dir', required=True, help='Directory containing input images')
    parser.add_argument('--facts-dir', required=True, help='Directory containing facts JSON files')
    parser.add_argument('--output-dir', required=True, help='Directory for output images')
    parser.add_argument('--comfyui-url', default='http://localhost:8188', help='ComfyUI server URL')
    parser.add_argument('--max-concurrent', type=int, default=2, help='Maximum concurrent tasks')
    parser.add_argument('--validate', action='store_true', help='Run quality validation after processing')
    parser.add_argument('--report-file', help='Output file for processing report')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = BatchGhostProcessor(args.comfyui_url)
    
    # Process batch
    try:
        summary = processor.process_batch(
            args.workflow,
            args.input_dir,
            args.facts_dir,
            args.output_dir,
            args.max_concurrent
        )
        
        # Run quality validation if requested
        if args.validate:
            print("\nRunning quality validation...")
            quality_report = processor.run_quality_validation(args.output_dir, args.facts_dir)
            summary["quality_validation"] = quality_report
        
        # Save report
        if args.report_file:
            with open(args.report_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"Processing report saved to {args.report_file}")
        
        # Print summary
        print(f"\nBatch Processing Summary:")
        print(f"Total tasks: {summary['total_tasks']}")
        print(f"Completed: {summary['completed_tasks']}")
        print(f"Failed: {summary['failed_tasks']}")
        print(f"Processing time: {summary['processing_time']:.1f} seconds")
        
        if args.validate and "quality_validation" in summary:
            qv = summary["quality_validation"]
            if "pass_rate" in qv:
                print(f"Quality validation pass rate: {qv['pass_rate']:.1f}%")
        
    except Exception as e:
        print(f"Batch processing failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
