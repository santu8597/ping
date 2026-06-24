"""
Celery task wrappers for scheduled jobs.

Each task wraps an existing scheduler function WITHOUT modifying its business logic.
Imports are lazy (inside functions) to avoid circular import issues with Django + Celery.
"""
import logging
import time

from celery import shared_task

logger = logging.getLogger('celery.tasks')


def _run_task(task_name, func):
    """Structured logging wrapper. Does NOT modify business logic."""
    logger.info(f"[TASK START] {task_name}")
    start = time.time()
    try:
        result = func()
        duration = time.time() - start
        logger.info(f"[TASK COMPLETE] {task_name} | duration={duration:.2f}s")
        return result
    except Exception as exc:
        duration = time.time() - start
        logger.error(
            f"[TASK FAILED] {task_name} | duration={duration:.2f}s | error={exc}",
            exc_info=True,
        )
        raise


@shared_task(name='backend.anchor.tasks.query_history_status_update_task')
def query_history_status_update_task():
    from backend.anchor.webservice.commend_execution_view import QueryHistoryStatusUpdateCorn
    _run_task('QueryHistoryStatusUpdateCorn', QueryHistoryStatusUpdateCorn)


@shared_task(name='backend.anchor.tasks.save_anchor_details_from_aiori_task')
def save_anchor_details_from_aiori_task():
    from backend.anchor.webservice.anchor_registration_view import SaveAnchorDetailsFromAIORICronClass
    _run_task('SaveAnchorDetailsFromAIORICronClass', SaveAnchorDetailsFromAIORICronClass)


@shared_task(name='backend.anchor.tasks.sync_anchor_ip_task')
def sync_anchor_ip_task():
    from backend.anchor.sync import sync_anchor_ip
    _run_task('sync_anchor_ip', sync_anchor_ip)


@shared_task(name='backend.anchor.tasks.sync_pending_measurements_task')
def sync_pending_measurements_task():
    from backend.anchor.sync import sync_pending_measurements
    _run_task('sync_pending_measurements', sync_pending_measurements)


@shared_task(name='backend.anchor.tasks.rd3mn_pin_command_execution_task')
def rd3mn_pin_command_execution_task():
    from backend.anchor.webservice.commend_execution_view import RD3MNPinCommandExecutionCornView
    _run_task('RD3MNPinCommandExecutionCornView', RD3MNPinCommandExecutionCornView)


@shared_task(name='backend.anchor.tasks.rd3mn_pin_command_execution_root_server_task')
def rd3mn_pin_command_execution_root_server_task():
    from backend.anchor.webservice.anycast_view import RD3MNPinCommandExecutionForRootServerCornView
    _run_task('RD3MNPinCommandExecutionForRootServerCornView', RD3MNPinCommandExecutionForRootServerCornView)


@shared_task(name='backend.anchor.tasks.root_server_pin_result_update_task')
def root_server_pin_result_update_task():
    from backend.anchor.webservice.anycast_view import RootServerPinResultUpdateCornView
    _run_task('RootServerPinResultUpdateCornView', RootServerPinResultUpdateCornView)
