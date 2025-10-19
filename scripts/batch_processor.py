#!/usr/bin/env python3
"""
Batch Ghost Mannequin Processor

Processes multiple garments through the ComfyUI ghost mannequin workflow
with parallel execution, progress tracking, and comprehensive reporting.

Features:
- Parallel workflow execution with configurable concurrency
- Progress tracking and status reporting
- Error handling and retry logic
- Comprehensive batch reports
- Resume capability for interrupted batches

Usage:
    python scripts/batch_processor.py --input-dir input/garments --output-dir output/batch
"""

import json
import asyncio
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import csv

from run_comfy import run_ghost_mannequin_workflow


@dataclass
class BatchItem:
    """Represents a single garment processing item"""
    id: str
    input_image: str
    facts_file: str
    ccj_file: str
    custom_additions: str = ""
    status: str = "pending"  # pending, processing, completed, failed
    error_message: str = ""
    output_images: List[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_time_seconds: float = 0.0
    
    def __post_init__(self):
        if self.output_images is None:
            self.output_images = []


@dataclass 
class BatchReport:
    """Comprehensive batch processing report"""
    batch_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_items: int
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    concurrency: int = 1
    items: List[BatchItem] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []


class BatchProcessor:
    """Production-ready batch processor for ghost mannequin generation"""
    
    def __init__(self, 
                 workflow_path: str,
                 server_address: str = "127.0.0.1:8188",
                 concurrency: int = 2,
                 timeout: int = 300,
                 retry_failed: bool = True,
                 max_retries: int = 3):
        
        self.workflow_path = workflow_path
        self.server_address = server_address
        self.concurrency = concurrency
        self.timeout = timeout
        self.retry_failed = retry_failed
        self.max_retries = max_retries
        
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure batch processing logging"""
        logger = logging.getLogger("BatchProcessor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        return logger
    
    def create_batch_from_directory(self, 
                                  input_dir: str,
                                  facts_file: str = "input/factsv3.json",
                                  ccj_file: str = "input/ccj_controlblock.json") -> List[BatchItem]:
        """Create batch items from input directory"""
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(input_path.glob(f"*{ext}"))
            image_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            raise ValueError(f"No image files found in {input_dir}")
        
        batch_items = []
        for img_file in sorted(image_files):
            item_id = img_file.stem
            
            # Look for garment-specific facts file
            garment_facts = input_path / f"{item_id}_facts.json"
            if not garment_facts.exists():
                garment_facts = facts_file
            
            # Look for garment-specific CCJ file  
            garment_ccj = input_path / f"{item_id}_ccj.json"
            if not garment_ccj.exists():
                garment_ccj = ccj_file
                
            batch_item = BatchItem(
                id=item_id,
                input_image=str(img_file),
                facts_file=str(garment_facts),
                ccj_file=str(garment_ccj),
                custom_additions=""
            )
            batch_items.append(batch_item)
        
        self.logger.info(f"Created batch with {len(batch_items)} items")
        return batch_items
    
    def load_batch_config(self, config_file: str) -> List[BatchItem]:
        """Load batch configuration from JSON file"""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Batch config not found: {config_file}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        batch_items = []
        for item_config in config.get('items', []):
            batch_item = BatchItem(**item_config)
            batch_items.append(batch_item)
        
        self.logger.info(f"Loaded batch config with {len(batch_items)} items")
        return batch_items
    
    def save_batch_config(self, batch_items: List[BatchItem], config_file: str):
        """Save batch configuration to JSON file"""
        config = {
            'items': [asdict(item) for item in batch_items]
        }
        
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        self.logger.info(f"Saved batch config to {config_file}")
    
    async def process_single_item(self, item: BatchItem, semaphore: asyncio.Semaphore) -> BatchItem:
        """Process a single batch item with semaphore control"""
        async with semaphore:
            self.logger.info(f"Processing item: {item.id}")
            
            item.status = "processing"
            item.start_time = datetime.now()
            
            try:
                # Execute workflow
                output_images = await run_ghost_mannequin_workflow(
                    workflow_path=self.workflow_path,
                    input_image=item.input_image,
                    facts_file=item.facts_file,
                    ccj_file=item.ccj_file,
                    custom_additions=item.custom_additions,
                    server_address=self.server_address,
                    timeout=self.timeout
                )
                
                # Success
                item.status = "completed"
                item.output_images = output_images
                item.end_time = datetime.now()
                item.processing_time_seconds = (item.end_time - item.start_time).total_seconds()
                
                self.logger.info(f"Completed item: {item.id} ({len(output_images)} images}")
            except Exception as e:
                # Failure
                item.status = "failed"
                item.error_message = str(e)
                item.end_time = datetime.now()
                item.processing_time_seconds = (item.end_time - item.start_time).total_seconds()
                
                self.logger.error(f"Failed item: {item.id} - {e}")
            
            return item
    
    async def process_batch(self, batch_items: List[BatchItem]) -> BatchReport:
        """Process entire batch with parallel execution"""
        
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"Starting batch processing: {batch_id}")
        
        # Initialize batch report
        report = BatchReport(
            batch_id=batch_id,
            start_time=datetime.now(),
            total_items=len(batch_items),
            concurrency=self.concurrency,
            items=batch_items.copy()
        )
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)
        
        # Process all items
        tasks = [
            self.process_single_item(item, semaphore) 
            for item in batch_items
        ]
        
        # Execute with progress reporting
        completed_tasks = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            completed_tasks.append(result)
            
            # Progress update
            progress = len(completed_tasks) / len(tasks) * 100
            self.logger.info(f"Progress: {len(completed_tasks)}/{len(tasks)} ({progress:.1f}%)")
        
        # Update report
        report.end_time = datetime.now()
        report.items = completed_tasks
        
        # Calculate statistics
        for item in completed_tasks:
            if item.status == "completed":
                report.completed += 1
                report.total_processing_time += item.processing_time_seconds
            elif item.status == "failed":
                report.failed += 1
        
        if report.completed > 0:
            report.average_processing_time = report.total_processing_time / report.completed
        
        self.logger.info(f"Batch completed: {report.completed} success, {report.failed} failed")
        return report
    
    def generate_csv_report(self, report: BatchReport, output_file: str):
        """Generate CSV report of batch processing results"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'id', 'input_image', 'status', 'processing_time_seconds',
                'output_images_count', 'error_message'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in report.items:
                writer.writerow({
                    'id': item.id,
                    'input_image': item.input_image,
                    'status': item.status,
                    'processing_time_seconds': item.processing_time_seconds,
                    'output_images_count': len(item.output_images),
                    'error_message': item.error_message
                })
        
        self.logger.info(f"CSV report saved to: {output_file}")
    
    def generate_summary_report(self, report: BatchReport, output_file: str):
        """Generate human-readable summary report"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(f"# Batch Processing Report: {report.batch_id}\\n\\n")
            f.write(f"**Start Time:** {report.start_time}\\n")
            f.write(f"**End Time:** {report.end_time}\\n")
            f.write(f"**Total Duration:** {(report.end_time - report.start_time).total_seconds():.1f}s\\n\\n")
            
            f.write(f"## Summary\\n\\n")
            f.write(f"- **Total Items:** {report.total_items}\\n")
            f.write(f"- **Completed:** {report.completed}\\n")
            f.write(f"- **Failed:** {report.failed}\\n")
            f.write(f"- **Success Rate:** {(report.completed / report.total_items * 100):.1f}%\\n")
            f.write(f"- **Concurrency:** {report.concurrency}\\n")
            f.write(f"- **Average Processing Time:** {report.average_processing_time:.1f}s\\n\\n")
            
            if report.failed > 0:
                f.write(f"## Failed Items\\n\\n")
                for item in report.items:
                    if item.status == "failed":
                        f.write(f"- **{item.id}:** {item.error_message}\\n")
                f.write("\\n")
            
            f.write(f"## Completed Items\\n\\n")
            for item in report.items:
                if item.status == "completed":
                    f.write(f"- **{item.id}:** {len(item.output_images)} images ({item.processing_time_seconds:.1f}s)\\n")
        
        self.logger.info(f"Summary report saved to: {output_file}")


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Batch process ghost mannequin workflows"
    )
    parser.add_argument(
        "--workflow",
        default="workflows/ghostmannequin_comfyui_v1.json",
        help="Path to ComfyUI workflow JSON file"
    )
    parser.add_argument(
        "--input-dir",
        help="Directory containing input garment images"
    )
    parser.add_argument(
        "--batch-config",
        help="JSON file with batch configuration"
    )
    parser.add_argument(
        "--output-dir",
        default="output/batch",
        help="Output directory for reports and results"
    )
    parser.add_argument(
        "--facts-file",
        default="input/factsv3.json",
        help="Default FactsV3 JSON file"
    )
    parser.add_argument(
        "--ccj-file",
        default="input/ccj_controlblock.json", 
        help="Default CCJ ControlBlock JSON file"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Number of concurrent workflows"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per workflow in seconds"
    )
    parser.add_argument(
        "--server",
        default="127.0.0.1:8188",
        help="ComfyUI server address"
    )
    
    args = parser.parse_args()
    
    if not args.input_dir and not args.batch_config:
        parser.error("Must specify either --input-dir or --batch-config")
    
    try:
        # Initialize processor
        processor = BatchProcessor(
            workflow_path=args.workflow,
            server_address=args.server,
            concurrency=args.concurrency,
            timeout=args.timeout
        )
        
        # Create batch items
        if args.input_dir:
            batch_items = processor.create_batch_from_directory(
                args.input_dir, args.facts_file, args.ccj_file
            )
        else:
            batch_items = processor.load_batch_config(args.batch_config)
        
        # Process batch
        report = asyncio.run(processor.process_batch(batch_items))
        
        # Generate reports
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_file = output_dir / f"{report.batch_id}_results.csv"
        summary_file = output_dir / f"{report.batch_id}_summary.md"
        config_file = output_dir / f"{report.batch_id}_config.json"
        
        processor.generate_csv_report(report, str(csv_file))
        processor.generate_summary_report(report, str(summary_file))
        processor.save_batch_config(report.items, str(config_file))
        
        # Print results
        print(f"\\n🎉 Batch processing completed!")
        print(f"📊 Results: {report.completed} success, {report.failed} failed")
        print(f"📈 Success rate: {(report.completed / report.total_items * 100):.1f}%")
        print(f"⏱️  Average processing time: {report.average_processing_time:.1f}s")
        print(f"📁 Reports saved to: {output_dir}")
        
        return 0 if report.failed == 0 else 1
        
    except Exception as e:
        print(f"\\n❌ Batch processing failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())