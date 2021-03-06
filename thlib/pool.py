import sys
import traceback
import logging
from thlib.side.Qt import QtCore


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s"
)

logger = logging.getLogger("connection.log")


class ThreadsPool(QtCore.QThread):
    # TODO add wake-up timer

    finished = QtCore.Signal()
    started = QtCore.Signal()

    def __init__(self, max_threads=1, parent=None):
        super(ThreadsPool, self).__init__(parent=parent)

        self.max_threads = max_threads
        self.poll_time = 10

        self._op_queue = []
        self._threads = []
        self._thread_free = 0
        self._started = False

    def reset_poll_timer(self):
        self.poll_time = self.idle_poll_time

    @property
    def is_started(self):
        return self._started

    @property
    def is_stopped(self):
        return not self._started

    def add_task(self, func, *args, **kwargs):

        if self._started:
            op = OperationWorker(func, *args, **kwargs)
            self._op_queue.append(op)
            return op

    def start(self):
        self._started = True

        self._threads = []
        for i in range(self.max_threads):
            self._threads.append(OperationThread(self))
            self._threads[i].start()
            self._thread_free += 1

        super(ThreadsPool, self).start()

    def exit(self):
        # frees ops queue and waits while queued threads running
        # stops polling
        self._started = False
        self._op_queue = []
        self._thread_free = 0

        for op_thread in self._threads:
            op_thread.stop_tasks()
            op_thread.exit()
            op_thread.wait()

        self._threads = []

        super(ThreadsPool, self).exit()

    def run(self):
        self.started.emit()
        while self._started:
            self.msleep(self.poll_time)
            for op_thread in self._threads:
                if op_thread.is_free:
                    if self._op_queue:
                        op = self._op_queue.pop(0)
                        op_thread.add(op)

                        self._thread_free -= 1
                    else:
                        self._thread_free += 1
                else:
                    self.finished.emit()


class OperationThread(QtCore.QThread):
    def __init__(self, parent=None):
        super(OperationThread, self).__init__(parent=parent)

        self._os_queue = []
        self._started = True

    @property
    def is_free(self):

        if self._os_queue:
            return False

        return True

    def add(self, op):
        self._started = True
        op.moveToThread(self.thread())
        self._os_queue.append(op)
        self.start()

    def stop_tasks(self):
        for op in self._os_queue:
            op.deleteLater()

        self._os_queue = []
        self._started = False

    def exit(self):
        self._op_queue = []
        self._started = False

        super(OperationThread, self).exit()

    def run(self):

        while self._started:
            while self._os_queue:
                op = self._os_queue.pop(0)

                # Here we wait for connections, and user fire .start()
                if op.is_started:
                    op.do_task()
                else:
                    # little wait before task started
                    self.msleep(50)
                    self._os_queue.append(op)
            else:
                self._started = False


class OperationWorker(QtCore.QObject):

    started = QtCore.Signal()
    finished = QtCore.Signal()
    error = QtCore.Signal(object)
    result = QtCore.Signal(object)
    progress = QtCore.Signal(object)
    stop = QtCore.Signal(object)

    def __init__(self, func, *args, **kwargs):
        super(OperationWorker, self).__init__()

        self._func = func
        self._args = args
        self._kwargs = kwargs
        self.signals_enabled = True
        self._started = False
        self._result = None
        self._data = None

    @property
    def is_started(self):
        return self._started

    def add_result_data(self, data):
        # will add another data into result output
        # only for tuple output
        self._data = data

    def connect_progress(self, func):
        # attaching progress signal to kwargs
        # func should have "progress_signal" kwarg
        self.progress.connect(func)
        self._kwargs['progress_signal'] = self.progress

    def get_result_data(self):
        return self._data

    def start(self):
        self._started = True

    def retry(self):
        print('This is dummy func, not implemented yet')

    def do_task(self):
        self.started.emit()

        try:
            if self.signals_enabled:

                self._result = self._func(*self._args, **self._kwargs)

                if self._data:
                    result = self._result + (self._data, )
                    self._result = result

                self.result.emit(self._result)
                self.finished.emit()

        except Exception as expected:
            if self.signals_enabled:
                traceback.print_exc(file=sys.stdout)

            stacktrace = traceback.format_exc()
            exception = {
                'exception': expected,
                'stacktrace': stacktrace,
            }
            self.error.emit((exception, self))

        self.deleteLater()
