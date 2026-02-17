from apminsight.logger import agentlogger
from apminsight.util import current_milli_time


class ErrorInfo:

    def __init__(self, exc):
        self.exc = exc
        self.stackframes = None
        self.time = current_milli_time()

    def get_type(self):
        if hasattr(type(self.exc), "__name__"):
            return type(self.exc).__name__

        return "Error"

    def get_time(self):
        return self.time

    def get_level(self):
        return "FATAL"

    def get_message(self):
        try:
            return str(self.exc)
        except Exception:
            agentlogger.exception("unable to get exc message")

        return ""

    def get_error_stack_frames(self):
        try:
            if self.stackframes:
                return self.stackframes

            frames = []
            tb = self.exc.__traceback__
            while tb is not None:
                file_name = tb.tb_frame.f_code.co_filename
                if "apminsight" not in file_name:
                    func_name = tb.tb_frame.f_code.co_name
                    line_no = tb.tb_lineno
                    frames.append(["", file_name, func_name, line_no])
                tb = tb.tb_next

            self.stackframes = frames
            return frames[-25:]

        except Exception:
            agentlogger.exception("unable to get exc stackframes")

        return []
