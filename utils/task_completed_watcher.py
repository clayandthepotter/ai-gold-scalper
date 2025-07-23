#!/usr/bin/env python3
"""
AI Gold Scalper - Task Completed Watcher
Phase 6: Production Integration & Infrastructure

Monitors completed tasks and handles post-completion activities like
notifications, cleanup, result processing, and triggering dependent tasks.
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import signal
import sys

# Import task classes from pending watcher
from task_pending_watcher import TaskStatus, TaskPriority, Task

class NotificationChannel(Enum):
    """Notification channel types"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    LOG = "log"

@dataclass
class NotificationConfig:
    """Notification configuration"""
    channels: List[NotificationChannel]
    email_settings: Optional[Dict[str, str]] = None
    telegram_settings: Optional[Dict[str, str]] = None
    webhook_url: Optional[str] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = [NotificationChannel.LOG]

class CompletionHandler:
    """Base class for task completion handlers"""
    
    def __init__(self, task_type: str):
        self.task_type = task_type
    
    async def handle_completion(self, task: Task) -> bool:
        """Handle task completion - override in subclasses"""
        raise NotImplementedError(f"Handle completion not implemented for {self.task_type}")
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can process the task"""
        return task.type == self.task_type

class ModelTrainingCompletionHandler(CompletionHandler):
    """Handler for completed model training tasks"""
    
    def __init__(self):
        super().__init__("model_training")
    
    async def handle_completion(self, task: Task) -> bool:
        """Handle model training completion"""
        try:
            if task.status == TaskStatus.COMPLETED and task.result:
                result = task.result
                model_name = task.data.get('model_name', 'unknown')
                
                # Log training results
                logging.info(f"Model training completed for {model_name}")
                logging.info(f"Total models: {result.get('total_models', 0)}")
                logging.info(f"Successful: {result.get('successful', 0)}")
                logging.info(f"Failed: {result.get('failed', 0)}")
                
                # Update model registry status
                self._update_model_registry_status(task)
                
                # Create performance report
                self._create_training_report(task)
                
                # Trigger dependent tasks if successful
                if result.get('successful', 0) > 0:
                    await self._trigger_dependent_tasks(task)
                
                return True
                
            elif task.status == TaskStatus.FAILED:
                # Handle training failure
                await self._handle_training_failure(task)
                return True
                
        except Exception as e:
            logging.error(f"Error handling model training completion: {e}")
            return False
        
        return False
    
    def _update_model_registry_status(self, task: Task):
        """Update model registry with training status"""
        try:
            # This would update the model registry database
            # with training completion status and metrics
            pass
        except Exception as e:
            logging.error(f"Failed to update model registry: {e}")
    
    def _create_training_report(self, task: Task):
        """Create detailed training report"""
        try:
            report_dir = Path("logs/training_reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = report_dir / f"training_completion_{task.id}.json"
            
            report_data = {
                'task_id': task.id,
                'model_name': task.data.get('model_name'),
                'completion_time': task.completed_at.isoformat() if task.completed_at else None,
                'duration_seconds': (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else 0,
                'status': task.status.value,
                'result': task.result,
                'configuration': task.data.get('config', {})
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logging.info(f"Training report created: {report_file}")
            
        except Exception as e:
            logging.error(f"Failed to create training report: {e}")
    
    async def _trigger_dependent_tasks(self, task: Task):
        """Trigger tasks that depend on successful training"""
        try:
            # Example: trigger model evaluation task
            from task_pending_watcher import TaskPendingWatcher
            
            watcher = TaskPendingWatcher()
            
            # Create model evaluation task
            eval_task_id = watcher.create_task(
                "model_evaluation",
                {
                    "model_name": task.data.get('model_name'),
                    "training_task_id": task.id
                },
                priority=TaskPriority.HIGH
            )
            
            logging.info(f"Triggered model evaluation task: {eval_task_id}")
            
        except Exception as e:
            logging.error(f"Failed to trigger dependent tasks: {e}")
    
    async def _handle_training_failure(self, task: Task):
        """Handle training task failure"""
        try:
            # Log failure details
            logging.error(f"Model training failed: {task.error_message}")
            
            # Create failure report
            failure_report = {
                'task_id': task.id,
                'model_name': task.data.get('model_name'),
                'failure_time': task.completed_at.isoformat() if task.completed_at else None,
                'error_message': task.error_message,
                'retry_count': task.retry_count,
                'configuration': task.data.get('config', {})
            }
            
            # Save failure report
            report_dir = Path("logs/failure_reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            failure_file = report_dir / f"training_failure_{task.id}.json"
            with open(failure_file, 'w') as f:
                json.dump(failure_report, f, indent=2)
            
            logging.info(f"Training failure report created: {failure_file}")
            
        except Exception as e:
            logging.error(f"Failed to handle training failure: {e}")

class DataBackupCompletionHandler(CompletionHandler):
    """Handler for completed data backup tasks"""
    
    def __init__(self):
        super().__init__("data_backup")
    
    async def handle_completion(self, task: Task) -> bool:
        """Handle data backup completion"""
        try:
            if task.status == TaskStatus.COMPLETED and task.result:
                result = task.result
                
                # Log backup results
                logging.info(f"Data backup completed")
                logging.info(f"Backup path: {result.get('backup_path')}")
                logging.info(f"Files backed up: {result.get('files_backed_up', 0)}")
                
                # Verify backup integrity
                backup_valid = self._verify_backup_integrity(result)
                
                if backup_valid:
                    # Update backup registry
                    self._update_backup_registry(task)
                    
                    # Clean up old backups if needed
                    self._cleanup_old_backups()
                    
                    # Schedule next backup
                    await self._schedule_next_backup(task)
                    
                else:
                    logging.error("Backup integrity verification failed")
                
                return True
                
            elif task.status == TaskStatus.FAILED:
                await self._handle_backup_failure(task)
                return True
                
        except Exception as e:
            logging.error(f"Error handling backup completion: {e}")
            return False
        
        return False
    
    def _verify_backup_integrity(self, result: Dict[str, Any]) -> bool:
        """Verify backup file integrity"""
        try:
            backup_path = Path(result.get('backup_path', ''))
            if not backup_path.exists():
                return False
            
            # Check if backup files exist and have reasonable sizes
            backed_up_files = result.get('files', [])
            
            for file_path in backed_up_files:
                file_obj = Path(file_path)
                if not file_obj.exists():
                    logging.error(f"Backup file missing: {file_path}")
                    return False
                
                # Check minimum file size (should not be empty for databases)
                if file_obj.suffix == '.db' and file_obj.stat().st_size < 1024:
                    logging.error(f"Backup file too small: {file_path}")
                    return False
            
            logging.info("Backup integrity verification passed")
            return True
            
        except Exception as e:
            logging.error(f"Backup integrity check failed: {e}")
            return False
    
    def _update_backup_registry(self, task: Task):
        """Update backup registry with completion info"""
        try:
            registry_file = Path("logs/backup_registry.json")
            registry_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing registry
            registry = []
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
            
            # Add new backup entry
            backup_entry = {
                'task_id': task.id,
                'backup_path': task.result.get('backup_path'),
                'backup_type': task.result.get('backup_type'),
                'created_at': task.completed_at.isoformat() if task.completed_at else None,
                'files_count': task.result.get('files_backed_up', 0),
                'verified': True  # Since we just verified it
            }
            
            registry.append(backup_entry)
            
            # Keep only last 50 entries
            registry = registry[-50:]
            
            # Save updated registry
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            
            logging.info("Backup registry updated")
            
        except Exception as e:
            logging.error(f"Failed to update backup registry: {e}")
    
    def _cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            backup_dir = Path("backups")
            if not backup_dir.exists():
                return
            
            # Get all backup directories (sorted by creation time)
            backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith('backup_')]
            backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the last 10 backups
            max_backups = 10
            if len(backup_dirs) > max_backups:
                old_backups = backup_dirs[max_backups:]
                
                for old_backup in old_backups:
                    import shutil
                    shutil.rmtree(old_backup)
                    logging.info(f"Cleaned up old backup: {old_backup}")
                
        except Exception as e:
            logging.error(f"Failed to cleanup old backups: {e}")
    
    async def _schedule_next_backup(self, task: Task):
        """Schedule the next backup task"""
        try:
            backup_type = task.data.get('backup_type', 'full')
            
            # Schedule next backup based on type
            if backup_type == 'full':
                # Schedule weekly full backup
                next_backup_time = datetime.now() + timedelta(days=7)
            else:
                # Schedule daily incremental backup
                next_backup_time = datetime.now() + timedelta(days=1)
            
            from task_pending_watcher import TaskPendingWatcher
            
            watcher = TaskPendingWatcher()
            next_task_id = watcher.create_task(
                "data_backup",
                task.data,  # Use same configuration
                priority=TaskPriority.LOW,
                scheduled_for=next_backup_time
            )
            
            logging.info(f"Scheduled next backup task: {next_task_id} for {next_backup_time}")
            
        except Exception as e:
            logging.error(f"Failed to schedule next backup: {e}")
    
    async def _handle_backup_failure(self, task: Task):
        """Handle backup task failure"""
        try:
            logging.error(f"Data backup failed: {task.error_message}")
            
            # Create failure alert
            failure_data = {
                'task_id': task.id,
                'backup_type': task.data.get('backup_type'),
                'failure_time': task.completed_at.isoformat() if task.completed_at else None,
                'error_message': task.error_message,
                'retry_count': task.retry_count
            }
            
            # This is critical - backup failures should be reported immediately
            await self._send_critical_alert("BACKUP FAILURE", failure_data)
            
        except Exception as e:
            logging.error(f"Failed to handle backup failure: {e}")
    
    async def _send_critical_alert(self, alert_type: str, data: Dict[str, Any]):
        """Send critical system alert"""
        try:
            # Log the alert
            logging.critical(f"{alert_type}: {json.dumps(data, indent=2)}")
            
            # Here you could add email, Telegram, or other notification integrations
            
        except Exception as e:
            logging.error(f"Failed to send critical alert: {e}")

class HealthCheckCompletionHandler(CompletionHandler):
    """Handler for completed health check tasks"""
    
    def __init__(self):
        super().__init__("health_check")
    
    async def handle_completion(self, task: Task) -> bool:
        """Handle health check completion"""
        try:
            if task.status == TaskStatus.COMPLETED and task.result:
                result = task.result
                overall_status = result.get('overall_status', 'unknown')
                issues = result.get('issues', [])
                
                # Log health check results
                logging.info(f"Health check completed - Status: {overall_status}")
                if issues:
                    logging.warning(f"Health check found {len(issues)} issues: {issues}")
                
                # Update system health registry
                self._update_health_registry(task)
                
                # Handle critical issues
                if overall_status == 'critical':
                    await self._handle_critical_health_issues(task)
                elif issues:
                    await self._handle_health_warnings(task)
                
                # Schedule next health check
                await self._schedule_next_health_check(task)
                
                return True
                
            elif task.status == TaskStatus.FAILED:
                await self._handle_health_check_failure(task)
                return True
                
        except Exception as e:
            logging.error(f"Error handling health check completion: {e}")
            return False
        
        return False
    
    def _update_health_registry(self, task: Task):
        """Update system health registry"""
        try:
            registry_file = Path("logs/health_registry.json")
            registry_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing registry
            registry = []
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
            
            # Add new health check entry
            health_entry = {
                'task_id': task.id,
                'timestamp': task.completed_at.isoformat() if task.completed_at else None,
                'overall_status': task.result.get('overall_status'),
                'components': task.result.get('components', {}),
                'issues_count': len(task.result.get('issues', [])),
                'check_type': task.data.get('check_type', 'full')
            }
            
            registry.append(health_entry)
            
            # Keep only last 100 entries
            registry = registry[-100:]
            
            # Save updated registry
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            
            logging.info("Health registry updated")
            
        except Exception as e:
            logging.error(f"Failed to update health registry: {e}")
    
    async def _handle_critical_health_issues(self, task: Task):
        """Handle critical health issues"""
        try:
            issues = task.result.get('issues', [])
            
            # Create critical alert
            alert_data = {
                'task_id': task.id,
                'timestamp': task.completed_at.isoformat() if task.completed_at else None,
                'overall_status': task.result.get('overall_status'),
                'critical_issues': issues,
                'components_status': task.result.get('components', {})
            }
            
            # Send critical alert
            logging.critical(f"CRITICAL HEALTH ISSUES DETECTED: {json.dumps(alert_data, indent=2)}")
            
            # Trigger emergency procedures if needed
            await self._trigger_emergency_procedures(alert_data)
            
        except Exception as e:
            logging.error(f"Failed to handle critical health issues: {e}")
    
    async def _handle_health_warnings(self, task: Task):
        """Handle health check warnings"""
        try:
            issues = task.result.get('issues', [])
            
            logging.warning(f"Health check warnings detected: {issues}")
            
            # Create remediation tasks for known issues
            await self._create_remediation_tasks(issues, task)
            
        except Exception as e:
            logging.error(f"Failed to handle health warnings: {e}")
    
    async def _trigger_emergency_procedures(self, alert_data: Dict[str, Any]):
        """Trigger emergency procedures for critical issues"""
        try:
            # Example emergency procedures:
            
            # 1. Create immediate backup if disk space critical
            if any('disk space' in str(issue).lower() for issue in alert_data.get('critical_issues', [])):
                from task_pending_watcher import TaskPendingWatcher
                
                watcher = TaskPendingWatcher()
                emergency_backup_id = watcher.create_task(
                    "data_backup",
                    {
                        "backup_type": "emergency",
                        "target_path": "emergency_backups"
                    },
                    priority=TaskPriority.EMERGENCY
                )
                
                logging.info(f"Emergency backup triggered: {emergency_backup_id}")
            
            # 2. Could trigger service restarts, alerts to admins, etc.
            
        except Exception as e:
            logging.error(f"Failed to trigger emergency procedures: {e}")
    
    async def _create_remediation_tasks(self, issues: List[str], task: Task):
        """Create tasks to remediate identified issues"""
        try:
            from task_pending_watcher import TaskPendingWatcher
            
            watcher = TaskPendingWatcher()
            
            for issue in issues:
                if 'disk space' in issue.lower():
                    # Create cleanup task
                    cleanup_task_id = watcher.create_task(
                        "system_cleanup",
                        {"cleanup_type": "disk_space"},
                        priority=TaskPriority.HIGH
                    )
                    logging.info(f"Created disk cleanup task: {cleanup_task_id}")
                
                elif 'database' in issue.lower():
                    # Create database maintenance task
                    db_task_id = watcher.create_task(
                        "database_maintenance",
                        {"maintenance_type": "integrity_check"},
                        priority=TaskPriority.HIGH
                    )
                    logging.info(f"Created database maintenance task: {db_task_id}")
            
        except Exception as e:
            logging.error(f"Failed to create remediation tasks: {e}")
    
    async def _schedule_next_health_check(self, task: Task):
        """Schedule the next health check"""
        try:
            check_type = task.data.get('check_type', 'full')
            
            # Schedule based on check type and current status
            if task.result.get('overall_status') == 'critical':
                # More frequent checks when critical
                next_check_time = datetime.now() + timedelta(minutes=30)
            elif check_type == 'full':
                # Regular full checks every 4 hours
                next_check_time = datetime.now() + timedelta(hours=4)
            else:
                # Quick checks every hour
                next_check_time = datetime.now() + timedelta(hours=1)
            
            from task_pending_watcher import TaskPendingWatcher
            
            watcher = TaskPendingWatcher()
            next_task_id = watcher.create_task(
                "health_check",
                {"check_type": "quick" if task.result.get('overall_status') == 'healthy' else "full"},
                priority=TaskPriority.NORMAL,
                scheduled_for=next_check_time
            )
            
            logging.info(f"Scheduled next health check: {next_task_id} for {next_check_time}")
            
        except Exception as e:
            logging.error(f"Failed to schedule next health check: {e}")
    
    async def _handle_health_check_failure(self, task: Task):
        """Handle health check failure"""
        try:
            logging.error(f"Health check failed: {task.error_message}")
            
            # This is concerning - health checks failing means we can't monitor the system
            failure_data = {
                'task_id': task.id,
                'failure_time': task.completed_at.isoformat() if task.completed_at else None,
                'error_message': task.error_message,
                'retry_count': task.retry_count
            }
            
            logging.critical(f"HEALTH CHECK SYSTEM FAILURE: {json.dumps(failure_data, indent=2)}")
            
        except Exception as e:
            logging.error(f"Failed to handle health check failure: {e}")

class NotificationService:
    """Service for sending notifications about completed tasks"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
    
    async def send_notification(self, task: Task, message: str, level: str = "INFO"):
        """Send notification about task completion"""
        try:
            # Send to all configured channels
            for channel in self.config.channels:
                if channel == NotificationChannel.LOG:
                    self._send_log_notification(task, message, level)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(task, message, level)
                elif channel == NotificationChannel.TELEGRAM:
                    await self._send_telegram_notification(task, message, level)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook_notification(task, message, level)
        
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
    
    def _send_log_notification(self, task: Task, message: str, level: str):
        """Send log notification"""
        log_message = f"Task {task.id} ({task.type}): {message}"
        
        if level == "CRITICAL":
            logging.critical(log_message)
        elif level == "ERROR":
            logging.error(log_message)
        elif level == "WARNING":
            logging.warning(log_message)
        else:
            logging.info(log_message)
    
    async def _send_email_notification(self, task: Task, message: str, level: str):
        """Send email notification"""
        if not self.config.email_settings:
            return
        
        try:
            # Email implementation would go here
            pass
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")
    
    async def _send_telegram_notification(self, task: Task, message: str, level: str):
        """Send Telegram notification"""
        if not self.config.telegram_settings:
            return
        
        try:
            # Telegram implementation would go here
            pass
        except Exception as e:
            logging.error(f"Failed to send Telegram notification: {e}")
    
    async def _send_webhook_notification(self, task: Task, message: str, level: str):
        """Send webhook notification"""
        if not self.config.webhook_url:
            return
        
        try:
            payload = {
                'task_id': task.id,
                'task_type': task.type,
                'status': task.status.value,
                'message': message,
                'level': level,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info("Webhook notification sent successfully")
            else:
                logging.error(f"Webhook notification failed: {response.status_code}")
        
        except Exception as e:
            logging.error(f"Failed to send webhook notification: {e}")

class TaskCompletedWatcher:
    """Main task completed watcher system"""
    
    def __init__(self, db_path: str = "data/tasks.db"):
        self.db_path = Path(db_path)
        
        # Completion handlers
        self.handlers: Dict[str, CompletionHandler] = {}
        
        # Notification service
        notification_config = NotificationConfig(
            channels=[NotificationChannel.LOG]
        )
        self.notification_service = NotificationService(notification_config)
        
        # Monitoring
        self.is_running = False
        self.monitor_thread = None
        self.monitor_interval = 5  # seconds
        
        # Processed tasks tracking (to avoid duplicate processing)
        self.processed_tasks = set()
        
        # Register default handlers
        self._register_default_handlers()
        
        logging.info("Task Completed Watcher initialized")
    
    def _register_default_handlers(self):
        """Register default completion handlers"""
        self.register_handler(ModelTrainingCompletionHandler())
        self.register_handler(DataBackupCompletionHandler())
        self.register_handler(HealthCheckCompletionHandler())
    
    def register_handler(self, handler: CompletionHandler):
        """Register a completion handler"""
        self.handlers[handler.task_type] = handler
        logging.info(f"Registered completion handler for task type: {handler.task_type}")
    
    def _get_completed_tasks(self) -> List[Task]:
        """Get recently completed tasks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get tasks completed in the last hour that we haven't processed yet
                cutoff_time = datetime.now() - timedelta(hours=1)
                
                cursor = conn.execute("""
                    SELECT id, type, priority, status, created_at, scheduled_for, 
                           started_at, completed_at, timeout_seconds, retry_count, 
                           max_retries, data, result, error_message, dependencies
                    FROM tasks 
                    WHERE status IN (?, ?, ?) AND completed_at >= ?
                    ORDER BY completed_at DESC
                """, (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, 
                     TaskStatus.TIMEOUT.value, cutoff_time))
                
                tasks = []
                for row in cursor.fetchall():
                    task_id = row[0]
                    
                    # Skip if already processed
                    if task_id in self.processed_tasks:
                        continue
                    
                    from task_pending_watcher import TaskPriority
                    
                    task = Task(
                        id=task_id,
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
                    
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            logging.error(f"Failed to get completed tasks: {e}")
            return []
    
    async def _process_completed_task(self, task: Task):
        """Process a completed task"""
        try:
            logging.info(f"Processing completed task: {task.id} ({task.type}) - {task.status.value}")
            
            # Get handler for this task type
            handler = self.handlers.get(task.type)
            
            if handler:
                # Process with specific handler
                success = await handler.handle_completion(task)
                
                if success:
                    logging.info(f"Successfully processed completed task: {task.id}")
                    
                    # Send success notification
                    message = f"Task completed successfully"
                    if task.status == TaskStatus.COMPLETED:
                        await self.notification_service.send_notification(task, message, "INFO")
                    elif task.status == TaskStatus.FAILED:
                        await self.notification_service.send_notification(task, f"Task failed: {task.error_message}", "ERROR")
                    elif task.status == TaskStatus.TIMEOUT:
                        await self.notification_service.send_notification(task, "Task timed out", "WARNING")
                    
                else:
                    logging.error(f"Handler failed to process task: {task.id}")
            
            else:
                # Generic processing for tasks without specific handlers
                logging.info(f"No specific handler for task type {task.type}, using generic processing")
                await self._generic_task_processing(task)
            
            # Mark as processed
            self.processed_tasks.add(task.id)
            
            # Clean up old processed task IDs (keep last 1000)
            if len(self.processed_tasks) > 1000:
                # Convert to list, sort, and keep last 1000
                sorted_tasks = sorted(list(self.processed_tasks))
                self.processed_tasks = set(sorted_tasks[-1000:])
            
        except Exception as e:
            logging.error(f"Error processing completed task {task.id}: {e}")
    
    async def _generic_task_processing(self, task: Task):
        """Generic processing for tasks without specific handlers"""
        try:
            # Log completion
            if task.status == TaskStatus.COMPLETED:
                logging.info(f"Generic task completed: {task.id} ({task.type})")
                message = "Task completed successfully"
                level = "INFO"
            elif task.status == TaskStatus.FAILED:
                logging.error(f"Generic task failed: {task.id} ({task.type}) - {task.error_message}")
                message = f"Task failed: {task.error_message}"
                level = "ERROR"
            elif task.status == TaskStatus.TIMEOUT:
                logging.warning(f"Generic task timed out: {task.id} ({task.type})")
                message = "Task timed out"
                level = "WARNING"
            
            # Send notification
            await self.notification_service.send_notification(task, message, level)
            
            # Save completion record
            self._save_completion_record(task)
            
        except Exception as e:
            logging.error(f"Generic task processing failed for {task.id}: {e}")
    
    def _save_completion_record(self, task: Task):
        """Save task completion record"""
        try:
            records_dir = Path("logs/completion_records")
            records_dir.mkdir(parents=True, exist_ok=True)
            
            record_file = records_dir / f"completion_{task.id}.json"
            
            record_data = {
                'task_id': task.id,
                'task_type': task.type,
                'status': task.status.value,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'duration_seconds': (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else 0,
                'retry_count': task.retry_count,
                'error_message': task.error_message,
                'result': task.result,
                'data': task.data
            }
            
            with open(record_file, 'w') as f:
                json.dump(record_data, f, indent=2)
            
        except Exception as e:
            logging.error(f"Failed to save completion record for {task.id}: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Get completed tasks
                completed_tasks = self._get_completed_tasks()
                
                # Process each completed task
                for task in completed_tasks:
                    asyncio.run(self._process_completed_task(task))
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logging.error(f"Monitor loop error: {e}")
                time.sleep(30)  # Longer sleep on error
    
    def start(self):
        """Start the completed task watcher"""
        if self.is_running:
            logging.warning("Task completed watcher already running")
            return
        
        logging.info("Starting Task Completed Watcher...")
        self.is_running = True
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        
        logging.info("Task Completed Watcher started")
    
    def stop(self):
        """Stop the completed task watcher"""
        logging.info("Stopping Task Completed Watcher...")
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=30)
        
        logging.info("Task Completed Watcher stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'is_running': self.is_running,
            'registered_handlers': list(self.handlers.keys()),
            'processed_tasks_count': len(self.processed_tasks),
            'monitor_interval_seconds': self.monitor_interval
        }

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logging.info("Received shutdown signal")
    sys.exit(0)

def main():
    """Run the task completed watcher"""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start watcher
    watcher = TaskCompletedWatcher()
    
    try:
        watcher.start()
        
        # Keep running
        while watcher.is_running:
            time.sleep(10)
            
            # Show status every 60 seconds
            status = watcher.get_system_status()
            logging.info(f"Completion Watcher Status - Running: {status['is_running']}, "
                        f"Handlers: {len(status['registered_handlers'])}, "
                        f"Processed: {status['processed_tasks_count']}")
        
    except KeyboardInterrupt:
        logging.info("Shutdown requested by user")
    finally:
        watcher.stop()

if __name__ == "__main__":
    main()
