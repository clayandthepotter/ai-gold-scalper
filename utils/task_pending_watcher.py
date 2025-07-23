#!/usr/bin/env python3
"""
AI Gold Scalper - Task Pending Watcher
Phase 6: Production Integration & Infrastructure

Monitors pending tasks and ensures they are processed in a timely manner.
Handles task prioritization, timeout management, and failure recovery.
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import signal
import sys

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class Task:
    """Task data structure"""
    id: str
    type: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 300  # 5 minutes default
    retry_count: int = 0
    max_retries: int = 3
    data: Dict[str, Any] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    dependencies: List[str] = None  # Task IDs that must complete first
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.dependencies is None:
            self.dependencies = []

class TaskProcessor:
    """Base class for task processors"""
    
    def __init__(self, task_type: str):
        self.task_type = task_type
    
    async def process(self, task: Task) -> Any:
        """Process a task - override in subclasses"""
        raise NotImplementedError(f"Process method not implemented for {self.task_type}")
    
    def can_process(self, task: Task) -> bool:
        """Check if this processor can handle the task"""
        return task.type == self.task_type

class ModelTrainingProcessor(TaskProcessor):
    """Processor for model training tasks"""
    
    def __init__(self):
        super().__init__("model_training")
    
    async def process(self, task: Task) -> Any:
        """Process model training task"""
        try:
            model_name = task.data.get('model_name', 'unknown')
            training_config = task.data.get('config', {})
            
            logging.info(f"Starting model training for: {model_name}")
            
            # Import and run training
            from scripts.training.automated_model_trainer import AutomatedModelTrainer, TrainingConfig
            
            config = TrainingConfig(**training_config)
            trainer = AutomatedModelTrainer(config)
            
            if model_name == 'all':
                results = trainer.train_all_models()
            else:
                results = [trainer.train_model(model_name)]
            
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            return {
                'total_models': len(results),
                'successful': len(successful),
                'failed': len(failed),
                'results': [asdict(r) for r in results]
            }
            
        except Exception as e:
            raise Exception(f"Model training failed: {str(e)}")

class DataBackupProcessor(TaskProcessor):
    """Processor for data backup tasks"""
    
    def __init__(self):
        super().__init__("data_backup")
    
    async def process(self, task: Task) -> Any:
        """Process data backup task"""
        try:
            backup_type = task.data.get('backup_type', 'full')
            target_path = Path(task.data.get('target_path', 'backups'))
            
            logging.info(f"Starting {backup_type} data backup to {target_path}")
            
            # Create backup directory
            backup_dir = target_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup databases
            databases = ['data/market_data.db', 'data/trades.db', 'models/registry.db']
            backed_up_files = []
            
            for db_path in databases:
                if Path(db_path).exists():
                    import shutil
                    backup_file = backup_dir / Path(db_path).name
                    shutil.copy2(db_path, backup_file)
                    backed_up_files.append(str(backup_file))
            
            # Backup model files
            if backup_type in ['full', 'models']:
                models_dir = Path('models')
                if models_dir.exists():
                    backup_models_dir = backup_dir / 'models'
                    backup_models_dir.mkdir(exist_ok=True)
                    
                    for model_file in models_dir.glob('*.pkl'):
                        import shutil
                        backup_file = backup_models_dir / model_file.name
                        shutil.copy2(model_file, backup_file)
                        backed_up_files.append(str(backup_file))
            
            return {
                'backup_path': str(backup_dir),
                'files_backed_up': len(backed_up_files),
                'backup_type': backup_type,
                'files': backed_up_files
            }
            
        except Exception as e:
            raise Exception(f"Data backup failed: {str(e)}")

class SystemHealthCheckProcessor(TaskProcessor):
    """Processor for system health check tasks"""
    
    def __init__(self):
        super().__init__("health_check")
    
    async def process(self, task: Task) -> Any:
        """Process system health check task"""
        try:
            check_type = task.data.get('check_type', 'full')
            
            logging.info(f"Running {check_type} system health check")
            
            health_report = {
                'timestamp': datetime.now().isoformat(),
                'check_type': check_type,
                'components': {},
                'overall_status': 'healthy',
                'issues': []
            }
            
            # Check database connectivity
            try:
                db_paths = ['data/market_data.db', 'data/trades.db']
                db_status = {}
                
                for db_path in db_paths:
                    if Path(db_path).exists():
                        with sqlite3.connect(db_path) as conn:
                            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                            table_count = cursor.fetchone()[0]
                            db_status[db_path] = {
                                'accessible': True,
                                'table_count': table_count
                            }
                    else:
                        db_status[db_path] = {
                            'accessible': False,
                            'table_count': 0
                        }
                        health_report['issues'].append(f"Database not found: {db_path}")
                
                health_report['components']['databases'] = db_status
                
            except Exception as e:
                health_report['issues'].append(f"Database check failed: {str(e)}")
            
            # Check model files
            try:
                models_dir = Path('models')
                model_files = list(models_dir.glob('*.pkl')) if models_dir.exists() else []
                
                health_report['components']['models'] = {
                    'model_files_count': len(model_files),
                    'models_directory_exists': models_dir.exists()
                }
                
                if not models_dir.exists():
                    health_report['issues'].append("Models directory does not exist")
                
            except Exception as e:
                health_report['issues'].append(f"Model files check failed: {str(e)}")
            
            # Check disk space
            try:
                import shutil
                disk_usage = shutil.disk_usage('.')
                free_gb = disk_usage.free / (1024**3)
                
                health_report['components']['disk'] = {
                    'free_space_gb': round(free_gb, 2),
                    'total_space_gb': round(disk_usage.total / (1024**3), 2),
                    'usage_percent': round((disk_usage.used / disk_usage.total) * 100, 2)
                }
                
                if free_gb < 1.0:  # Less than 1GB free
                    health_report['issues'].append("Low disk space warning")
                
            except Exception as e:
                health_report['issues'].append(f"Disk space check failed: {str(e)}")
            
            # Determine overall status
            if health_report['issues']:
                health_report['overall_status'] = 'degraded' if len(health_report['issues']) <= 2 else 'critical'
            
            return health_report
            
        except Exception as e:
            raise Exception(f"Health check failed: {str(e)}")

class TaskPendingWatcher:
    """Main task pending watcher system"""
    
    def __init__(self, db_path: str = "data/tasks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Task processing
        self.processors: Dict[str, TaskProcessor] = {}
        self.processing_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, Task] = {}
        
        # Worker threads
        self.is_running = False
        self.worker_threads = []
        self.max_workers = 4
        
        # Monitoring
        self.monitor_thread = None
        self.monitor_interval = 10  # seconds
        
        # Task timeouts
        self.timeout_checks = {}
        
        # Initialize database
        self._init_database()
        
        # Register default processors
        self._register_default_processors()
        
        logging.info("Task Pending Watcher initialized")
    
    def _init_database(self):
        """Initialize tasks database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        scheduled_for DATETIME,
                        started_at DATETIME,
                        completed_at DATETIME,
                        timeout_seconds INTEGER DEFAULT 300,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        data TEXT,
                        result TEXT,
                        error_message TEXT,
                        dependencies TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tasks_status_priority 
                    ON tasks(status, priority DESC, created_at)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tasks_scheduled 
                    ON tasks(scheduled_for)
                """)
                
                conn.commit()
                logging.info("Tasks database initialized")
                
        except Exception as e:
            logging.error(f"Failed to initialize tasks database: {e}")
    
    def _register_default_processors(self):
        """Register default task processors"""
        self.register_processor(ModelTrainingProcessor())
        self.register_processor(DataBackupProcessor())
        self.register_processor(SystemHealthCheckProcessor())
    
    def register_processor(self, processor: TaskProcessor):
        """Register a task processor"""
        self.processors[processor.task_type] = processor
        logging.info(f"Registered processor for task type: {processor.task_type}")
    
    def create_task(self, task_type: str, data: Dict[str, Any], 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   scheduled_for: Optional[datetime] = None,
                   timeout_seconds: int = 300,
                   max_retries: int = 3,
                   dependencies: List[str] = None) -> str:
        """Create a new task"""
        
        task_id = f"{task_type}_{int(time.time())}_{hash(json.dumps(data, sort_keys=True)) % 10000}"
        
        task = Task(
            id=task_id,
            type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            scheduled_for=scheduled_for,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            data=data,
            dependencies=dependencies or []
        )
        
        self._save_task(task)
        logging.info(f"Created task: {task_id} ({task_type})")
        
        return task_id
    
    def _save_task(self, task: Task):
        """Save task to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tasks 
                    (id, type, priority, status, created_at, scheduled_for, started_at, 
                     completed_at, timeout_seconds, retry_count, max_retries, 
                     data, result, error_message, dependencies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.id, task.type, task.priority.value, task.status.value,
                    task.created_at, task.scheduled_for, task.started_at,
                    task.completed_at, task.timeout_seconds, task.retry_count,
                    task.max_retries, json.dumps(task.data) if task.data else None,
                    json.dumps(task.result) if task.result else None,
                    task.error_message, json.dumps(task.dependencies)
                ))
                conn.commit()
                
        except Exception as e:
            logging.error(f"Failed to save task {task.id}: {e}")
    
    def _load_task(self, task_id: str) -> Optional[Task]:
        """Load task from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, type, priority, status, created_at, scheduled_for, 
                           started_at, completed_at, timeout_seconds, retry_count, 
                           max_retries, data, result, error_message, dependencies
                    FROM tasks WHERE id = ?
                """, (task_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return Task(
                    id=row[0],
                    type=row[1],
                    priority=TaskPriority(row[2]),
                    status=TaskStatus(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    scheduled_for=datetime.fromisoformat(row[5]) if row[5] else None,
                    started_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    timeout_seconds=row[8],
                    retry_count=row[9],
                    max_retries=row[10],
                    data=json.loads(row[11]) if row[11] else {},
                    result=json.loads(row[12]) if row[12] else None,
                    error_message=row[13],
                    dependencies=json.loads(row[14]) if row[14] else []
                )
                
        except Exception as e:
            logging.error(f"Failed to load task {task_id}: {e}")
            return None
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks ready for processing"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.now()
                cursor = conn.execute("""
                    SELECT id FROM tasks 
                    WHERE status = ? AND (scheduled_for IS NULL OR scheduled_for <= ?)
                    ORDER BY priority DESC, created_at ASC
                """, (TaskStatus.PENDING.value, now))
                
                task_ids = [row[0] for row in cursor.fetchall()]
                tasks = []
                
                for task_id in task_ids:
                    task = self._load_task(task_id)
                    if task and self._are_dependencies_met(task):
                        tasks.append(task)
                
                return tasks
                
        except Exception as e:
            logging.error(f"Failed to get pending tasks: {e}")
            return []
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        if not task.dependencies:
            return True
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for dep_id in task.dependencies:
                    cursor = conn.execute("""
                        SELECT status FROM tasks WHERE id = ?
                    """, (dep_id,))
                    
                    row = cursor.fetchone()
                    if not row or TaskStatus(row[0]) != TaskStatus.COMPLETED:
                        return False
                
                return True
                
        except Exception as e:
            logging.error(f"Failed to check dependencies for task {task.id}: {e}")
            return False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Check for new pending tasks
                pending_tasks = self.get_pending_tasks()
                
                for task in pending_tasks:
                    if task.id not in self.active_tasks:
                        # Add to processing queue
                        priority = -task.priority.value  # Negative for max priority queue
                        self.processing_queue.put((priority, task.created_at, task.id))
                        logging.info(f"Queued task for processing: {task.id}")
                
                # Check for timeout tasks
                self._check_timeouts()
                
                # Clean up completed tasks older than 24 hours
                self._cleanup_old_tasks()
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logging.error(f"Monitor loop error: {e}")
                time.sleep(30)  # Longer sleep on error
    
    def _check_timeouts(self):
        """Check for timed out tasks"""
        current_time = datetime.now()
        
        for task_id, start_time in list(self.timeout_checks.items()):
            task = self.active_tasks.get(task_id)
            if not task:
                # Clean up orphaned timeout check
                del self.timeout_checks[task_id]
                continue
            
            elapsed = (current_time - start_time).total_seconds()
            if elapsed > task.timeout_seconds:
                logging.warning(f"Task {task_id} has timed out after {elapsed:.1f}s")
                
                # Mark as timeout
                task.status = TaskStatus.TIMEOUT
                task.completed_at = current_time
                task.error_message = f"Task timed out after {elapsed:.1f} seconds"
                
                self._save_task(task)
                
                # Remove from active tasks
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                if task_id in self.timeout_checks:
                    del self.timeout_checks[task_id]
                
                # Retry if possible
                if task.retry_count < task.max_retries:
                    self._retry_task(task)
    
    def _retry_task(self, task: Task):
        """Retry a failed task"""
        task.retry_count += 1
        task.status = TaskStatus.PENDING
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        
        self._save_task(task)
        logging.info(f"Retrying task {task.id} (attempt {task.retry_count}/{task.max_retries})")
    
    def _cleanup_old_tasks(self):
        """Clean up completed tasks older than 24 hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM tasks 
                    WHERE status IN (?, ?, ?) AND completed_at < ?
                """, (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, 
                     TaskStatus.TIMEOUT.value, cutoff_time))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logging.info(f"Cleaned up {deleted_count} old tasks")
                    
        except Exception as e:
            logging.error(f"Failed to cleanup old tasks: {e}")
    
    def _worker_loop(self, worker_id: int):
        """Worker thread loop"""
        logging.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get task from queue (with timeout)
                try:
                    priority, created_at, task_id = self.processing_queue.get(timeout=5)
                except queue.Empty:
                    continue
                
                # Load task
                task = self._load_task(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # Get processor
                processor = self.processors.get(task.type)
                if not processor:
                    logging.error(f"No processor found for task type: {task.type}")
                    task.status = TaskStatus.FAILED
                    task.error_message = f"No processor available for task type: {task.type}"
                    self._save_task(task)
                    continue
                
                # Mark as processing
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                self._save_task(task)
                
                self.active_tasks[task_id] = task
                self.timeout_checks[task_id] = task.started_at
                
                logging.info(f"Worker {worker_id} processing task: {task_id}")
                
                try:
                    # Process task
                    result = asyncio.run(processor.process(task))
                    
                    # Mark as completed
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    task.result = result
                    task.error_message = None
                    
                    logging.info(f"Worker {worker_id} completed task: {task_id}")
                    
                except Exception as e:
                    # Mark as failed
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    task.error_message = str(e)
                    
                    logging.error(f"Worker {worker_id} failed to process task {task_id}: {e}")
                    
                    # Retry if possible
                    if task.retry_count < task.max_retries:
                        self._retry_task(task)
                        continue
                
                # Save final state
                self._save_task(task)
                
                # Clean up
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                if task_id in self.timeout_checks:
                    del self.timeout_checks[task_id]
                
                self.processing_queue.task_done()
                
            except Exception as e:
                logging.error(f"Worker {worker_id} error: {e}")
                time.sleep(5)
        
        logging.info(f"Worker {worker_id} stopped")
    
    def start(self):
        """Start the task watcher"""
        if self.is_running:
            logging.warning("Task watcher already running")
            return
        
        logging.info("Starting Task Pending Watcher...")
        self.is_running = True
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        
        # Start worker threads
        for i in range(self.max_workers):
            worker_thread = threading.Thread(target=self._worker_loop, args=(i,))
            worker_thread.start()
            self.worker_threads.append(worker_thread)
        
        logging.info(f"Task Pending Watcher started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the task watcher"""
        logging.info("Stopping Task Pending Watcher...")
        self.is_running = False
        
        # Stop monitor thread
        if self.monitor_thread:
            self.monitor_thread.join(timeout=30)
        
        # Stop worker threads
        for worker_thread in self.worker_threads:
            worker_thread.join(timeout=30)
        
        self.worker_threads.clear()
        
        logging.info("Task Pending Watcher stopped")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self._load_task(task_id)
        if not task:
            return None
        
        return {
            'id': task.id,
            'type': task.type,
            'status': task.status.value,
            'priority': task.priority.value,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'retry_count': task.retry_count,
            'max_retries': task.max_retries,
            'error_message': task.error_message,
            'result': task.result
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count tasks by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) FROM tasks 
                    GROUP BY status
                """)
                
                status_counts = dict(cursor.fetchall())
                
                # Get recent tasks
                cursor = conn.execute("""
                    SELECT type, COUNT(*) FROM tasks 
                    WHERE created_at >= datetime('now', '-24 hours')
                    GROUP BY type
                """)
                
                recent_by_type = dict(cursor.fetchall())
                
                return {
                    'is_running': self.is_running,
                    'active_workers': len([t for t in self.worker_threads if t.is_alive()]),
                    'max_workers': self.max_workers,
                    'active_tasks': len(self.active_tasks),
                    'queue_size': self.processing_queue.qsize(),
                    'registered_processors': list(self.processors.keys()),
                    'task_counts_by_status': status_counts,
                    'recent_tasks_by_type': recent_by_type,
                    'timeout_checks': len(self.timeout_checks)
                }
                
        except Exception as e:
            logging.error(f"Failed to get system status: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e)
            }

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logging.info("Received shutdown signal")
    sys.exit(0)

def main():
    """Run the task pending watcher"""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start watcher
    watcher = TaskPendingWatcher()
    
    try:
        watcher.start()
        
        # Create some demo tasks
        logging.info("Creating demo tasks...")
        
        # Health check task
        watcher.create_task(
            "health_check",
            {"check_type": "full"},
            priority=TaskPriority.HIGH
        )
        
        # Model training task (scheduled for 30 seconds from now)
        scheduled_time = datetime.now() + timedelta(seconds=30)
        watcher.create_task(
            "model_training",
            {
                "model_name": "random_forest",
                "config": {
                    "min_samples": 50,
                    "hyperopt_trials": 10
                }
            },
            priority=TaskPriority.NORMAL,
            scheduled_for=scheduled_time
        )
        
        # Data backup task
        watcher.create_task(
            "data_backup",
            {
                "backup_type": "full",
                "target_path": "backups"
            },
            priority=TaskPriority.LOW
        )
        
        # Keep running
        while watcher.is_running:
            time.sleep(10)
            
            # Show status every 60 seconds
            status = watcher.get_system_status()
            logging.info(f"System Status - Active: {status['active_tasks']}, "
                        f"Queue: {status['queue_size']}, "
                        f"Workers: {status['active_workers']}")
        
    except KeyboardInterrupt:
        logging.info("Shutdown requested by user")
    finally:
        watcher.stop()

if __name__ == "__main__":
    main()
