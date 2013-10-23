# -*- coding: utf-8 -*-
'''Asynchronous task queue module.'''

from celery import Celery
from celery.utils.log import get_task_logger

celery = Celery()

# TODO: Hardcoded settings module. Should be set using framework's config handler
celery.config_from_object('website.settings')

@celery.task
def error_handler(task_id, task_name):
    """logs detailed message about tasks that raise exceptions

    :param task_id: TaskID of the failed task
    :param task_name: name of task that failed
    """
    # get the current logger
    logger = get_task_logger(__name__)
    # query the broker for the AsyncResult
    result = celery.AsyncResult(task_id)
    excep = result.get(propagate=False)
    # log detailed error mesage in error log
    logger.error('#####FAILURE LOG BEGIN#####\n'
                'Task {0} raised exception: {0}\n\{0}\n'
                '#####FAILURE LOG STOP#####'.format(task_name, excep, result.traceback))
