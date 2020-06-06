## Thank you! https://stackoverflow.com/questions/21617249/read-subprocess-stdout-and-stderr-concurrently
import threading
import queue as Queue


class ProcessIOReader:

    def join(self):
        self.te.join()
        self.to.join()
        self.running = False
        self.aggregator.join()
        # self.ti.join()

    def enqueue_in(self):
        while self.running and self.p.stdin is not None:
            while not self.stdin_queue.empty():
                s = self.stdin_queue.get()
                self.p.stdin.write(str(s) + '\n\r')
            pass

    def enqueue_output(self):
        if not self.p.stdout or self.p.stdout.closed:
            return
        out = self.p.stdout
        for line in iter(out.readline, b''):
            self.qo.put(line)
            out.flush()     # modified on 06-05-2020 SG, DN, WV

    def enqueue_err(self):
        if not self.p.stderr or self.p.stderr.closed:
            return
        err = self.p.stderr
        for line in iter(err.readline, b''):
            self.qe.put(line)
            err.flush()     # modified on 06-05-2020 SG, DN, WV

    def aggregate(self, merge_queue):
        while (self.running):
            self.merge_queues(merge_queue)
        self.merge_queues(merge_queue)

    def merge_queues(self, merge_queue):
        line = ""
        try:
            while self.qe.not_empty:
                line = self.qe.get_nowait()  # or q.get(timeout=.1)
                merge_queue.put(line)
                # self.unbblocked_err += line
        except Queue.Empty:
            pass

        line = ""
        try:
            while self.qo.not_empty:
                line = self.qo.get_nowait()  # or q.get(timeout=.1)
                merge_queue.put(line)
        except Queue.Empty:
            pass

    def update(self):
        line = ""
        try:
            while self.qe.not_empty:
                line = self.qe.get_nowait()  # or q.get(timeout=.1)
                self.unbblocked_err += line
        except Queue.Empty:
            pass

        line = ""
        try:
            while self.qo.not_empty:
                line = self.qo.get_nowait()  # or q.get(timeout=.1)
                self.unbblocked_out += line
        except Queue.Empty:
            pass

        while not self.stdin_queue.empty():
                s = self.stdin_queue.get()
                self.p.stdin.write(str(s))

    def get_stdout(self, clear=True):
        ret = self.unbblocked_out
        if clear:
            self.unbblocked_out = ""
        return ret

    def has_stdout(self):
        ret = self.get_stdout(False)
        if ret == '':
            return None
        else:
            return ret

    def get_stderr(self, clear=True):
        ret = self.unbblocked_out
        if clear:
            self.unbblocked_out = ""
        return ret

    def has_stderr(self):
        ret = self.get_stdout(False)
        if ret == '':
            return None
        else:
            return ret

    def __init__(self, subp, out_queue, name):
        '''This is a simple class that collects and aggregates the
        output from a subprocess so that you can more reliably use
        the class without having to block for subprocess.communicate.'''
        self.p = subp
        self.unbblocked_out = ""
        self.unbblocked_err = ""
        self.running = True
        self.qo = Queue.Queue()
        self.to = threading.Thread( name=f"out_read_{name}",
                                    target=self.enqueue_output,
                                    args=())
        self.to.daemon = True  # thread dies with the program
        self.to.start()

        self.qe = Queue.Queue()
        self.te = threading.Thread(name=f"err_read_{name}",
                                   target=self.enqueue_err,
                                   args=())
        self.te.daemon = True  # thread dies with the program
        self.te.start()

        self.stdin_queue = Queue.Queue()
        self.aggregator = threading.Thread(name=f"aggregate_{name}",
                                           target=self.aggregate,
                                           args=[out_queue])
        self.aggregator.daemon = True  # thread dies with the program
        self.aggregator.start()
