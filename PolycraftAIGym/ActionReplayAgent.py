import os, subprocess, socket, time

class ActionReplayAgent(object):

    def __init__(self, host, port, action_list=[], arg_list=[]):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.actionList = action_list;
        self.argList = arg_list;

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if 'PAL_PORT' in os.environ:
            self.sock.connect((self.host, int(os.environ['PAL_PORT'])))
            print('Using Port: ' + os.environ['PAL_PORT'])
        else:
            self.sock.connect((self.host, self.port))
            print('Using Port: ' + str(self.port))

    def act(self, delay=0.07):
        time.sleep(3)
        while len(self.actionList) > 0:  # main loop
            time.sleep(delay)
            userInput = self.actionList.pop(0) + ' ' + self.argList.pop(0)

            if str(userInput).lower().startswith("place_block"):
                userInput = "place" + userInput[11:]

            self.sock.send(str.encode(userInput + '\n'))

            # Look for the response
            if True:
                BUFF_SIZE = 4096  # 4 KiB
                data = b''
                while True:
                    part = self.sock.recv(BUFF_SIZE)
                    data += part
                    if len(part) < BUFF_SIZE:
                        # either 0 or end of data
                        break
                print(data)