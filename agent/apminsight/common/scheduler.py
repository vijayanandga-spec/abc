import sched
import time
from threading import Thread
from apminsight.logger import agentlogger

class Scheduler:
    def __init__(self):
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self.running = False
        self.scheduled_tasks = set()  # Track scheduled tasks


    def add_task(self, interval, method, repeat=True, arguments = (), **kwargs):
        """
        Add a task to the scheduler.

        :param interval: Time interval in seconds between method executions.
        :param method: The method to be executed.
        :param repeat: Whether the task should repeat (default: True).
        :param args: Positional arguments for the method.
        :param kwargs: Keyword arguments for the method.
        """
        
        task_id = (method, arguments, tuple(kwargs.items()))  # Unique identifier for the task

        if task_id in self.scheduled_tasks:
            agentlogger.debug(f"Task {method.__name__} is already scheduled. Skipping duplicate.")
            return

        self.scheduled_tasks.add(task_id)

        def wrapper():
            method(*arguments, **kwargs)
            if repeat:
                self._scheduler.enter(interval, 1, wrapper)

        agentlogger.debug(f"Scheduling task: {method.__name__} to run every {interval} seconds")
        self._scheduler.enter(interval, 1, wrapper)


    def remove_task(self, method, arguments=(), **kwargs):
        """
        Remove a scheduled task from the scheduler.

        :param method: The method to be removed.
        :param arguments: Positional arguments for the method.
        :param kwargs: Keyword arguments for the method.
        """
        task_id = (method, arguments, tuple(kwargs.items()))  # Unique identifier for the task

        if task_id in self.scheduled_tasks:
            event = self.scheduled_tasks.pop(task_id)
            try:
                self._scheduler.cancel(event)
                agentlogger.debug(f"Task {method.__name__} removed successfully.")
            except ValueError:
                agentlogger.debug(f"Task {method.__name__} could not be removed (not found in scheduler).")
        else:
            agentlogger.debug(f"Task {method.__name__} not found in scheduled tasks.")


    def start(self):
        """
        Start the scheduler in a separate thread.
        """
        if self.running:
            return
        self.running = True
        def run_scheduler():
            while self.running:
                self._scheduler.run(blocking=False)
                time.sleep(1)

        Thread(target=run_scheduler, daemon=True).start()

    def stop(self):
        """
        Stop the scheduler.
        """
        self.running = False
