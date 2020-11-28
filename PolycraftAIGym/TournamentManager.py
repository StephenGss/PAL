import threading, socket, json, os

HOST = "127.0.0.1"
TM_PORT = 9005

class TournamentThread(threading.Thread):
    def __init__(self, queue, tm_lock, args=(), kwargs=None):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.queue = queue
        self.tm_lock = tm_lock
        self.receive_messages = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if 'PAL_TM_PORT' in os.environ:
            self.sock.connect((HOST, int(os.environ['PAL_TM_PORT'])))
            print('Using Port: ' + os.environ['PAL_TM_PORT'])
        else:
            self.sock.connect((HOST, TM_PORT))
            print('Using Port: ' + str(TM_PORT))

    def kill(self):
        self.queue.put(None)

    def run(self):
        print(threading.currentThread().getName(), self.receive_messages)
        print("Initializing TM Thread")

        while True:
            val = self.queue.get()
            if val is None:  # If you send `None`, the thread will exit.
                return
            self.do_thing_with_message(val)

    def do_thing_with_message(self, message):
        if self.receive_messages:
            with self.tm_lock:
                print(threading.currentThread().getName(), "Received {}".format(message))
                # send the command to PAL
                self.sock.send(str.encode(message + '\n'))

                BUFF_SIZE = 4096  # 4 KiB
                data = b''
                while True:
                    part = self.sock.recv(BUFF_SIZE)
                    data += part
                    if len(part) < BUFF_SIZE:
                        # either 0 or end of data
                        break
                if data is None or data == "":
                    print(threading.currentThread().getName(), "ERROR: received empty string")
                    return
                data_dict = json.loads(data)
                print(data_dict)
