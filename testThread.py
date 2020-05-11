import threading, socket, subprocess, sys

class TestThread(threading.Thread):
    def __init__(self, command, args=(), kwargs=None):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.command = command

    def run(self):
        print("Initializing Agent Thread: " + self.command)
        # agent = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE)

        log = open('agent_log.txt', 'w')
        agent = subprocess.Popen(["python", "hg_agent.py"], shell=False, stdout=log, stderr=log)
        while True:
            # grab the console output of PAL
            # next_line = agent.stdout.readline()

            # first check if we crashed or something... hopefully  this doesn't happen
            if agent.poll() is not None:
                break

            # if len(str(next_line)) > 3:
            #     # print for debugging
            #     sys.stdout.write("[AGENT] " + str(next_line) + '\n')
            #     sys.stdout.flush()

