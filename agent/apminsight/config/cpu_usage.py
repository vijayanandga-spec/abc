import os
import threading
import time
from apminsight.constants import PROCESS_CPU_THRESHOLD_VAL
from apminsight.logger import agentlogger
from apminsight.util import get_module

   
class CPUUtilization:

    def __init__(self, cpu_threshold=PROCESS_CPU_THRESHOLD_VAL):
        self.cpu_threshold_status = False
        self.cpu_threshold_val = cpu_threshold
        self.proc_cpu_percent = 0.0
        self._lock = threading.Lock()
        self._psutil = self.get_psutil()
        self._process = self._psutil.Process(os.getpid()) if self._psutil else None
        self._num_cores = self._psutil.cpu_count(logical=True) if self._psutil else 1
        
    def get_proc_cpu_percent(self,interval=0.1):
        try :
            if self._psutil is not None:
                if self._process is None or self._process.pid == os.getpid():
                    self._process =self._psutil.Process(os.getpid())
                self.proc_cpu_percent = self._process.cpu_percent(interval=interval)/self._num_cores
        except Exception as e:
            agentlogger.error(f"Error in caluclating proc_cpu_percent: {e}")

        agentlogger.info(f"CPU Utilization for process with PID {os.getpid()}: {self.proc_cpu_percent}%")
        return self.proc_cpu_percent

            
    def get_psutil(self):
        psutil = get_module('psutil')
        return psutil if psutil is not None else get_module('apminsight.dependency.psutil')
        
    def start_cpu_stats_thread(self):
        if self._psutil is not None:
            self._process = self._psutil.Process(os.getpid())
            self._num_cores = self._psutil.cpu_count(logical=True)
            self.thread = threading.Thread(target=self.cpu_utilization, daemon=True)
            self.thread.start()
            self._thread_status = True

    def get_cpu_threshold_status(self):
        return True if self.proc_cpu_percent > self.cpu_threshold_val else False

    def cpu_utilization(self):
        agentlogger.info("CPU utilization stats thread started")
        while True:
            try:
                with self._lock:
                    self._proc_cpu_percent = self.get_proc_cpu_percent()
                    agentlogger.info(f"CPU Utilization for process with PID {os.getpid()}: {self._proc_cpu_percent}%")
            except Exception as exc:
                agentlogger.info(f"Exception in CPU utilization thread {exc}%")
            finally:
                time.sleep(60)
