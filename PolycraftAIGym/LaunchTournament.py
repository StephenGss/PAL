import subprocess, threading, socket
import sys
import TournamentManager
import testThread
import queue
from queue import Queue
from enum import Enum
import json
from subprocess import PIPE


class LaunchTournament:

    def __init__(self, args=(), kwargs=None):
        self.commands_sent = 0

    def analyze_line(self, line):
        return None

    def check_ended(self, line):
        # TODO: Track stepcost to call reset
        # TODO: Track total reward to call reset
        # TODO: Track total run time to call reset
        # TODO: Track agent giveup to call reset
        # TODO: Track end condition flag to call reset
        self.commands_sent += 1

        # steps greater than 60, END
        if line.find('{') != -1:
            json_text = line[line.find('{'):line.find('\\r\\n')]
            data_dict = json.loads(json_text)
            if data_dict["goal"]["goalAchieved"]:
                return True
            if self.commands_sent > 50:
                return True

        return None


    def read_output(self, pipe, q):
        """reads output from `pipe`, when line has been read, puts
    line on Queue `q`"""

        while True:
            l = pipe.readline()
            q.put(l)


    def execute(self):
        processes = []
        # pal_client_process = subprocess.Popen(command, shell=True, cwd='../', stdout=subprocess.PIPE)

        # log_pal = open('pal_log.txt', 'w+')
        pal_client_process = subprocess.Popen("gradlew runclient", shell=True, cwd='../', stdout=subprocess.PIPE,
                                              stdin=subprocess.PIPE)
        agent = None
        q = queue.Queue()
        q2 = queue.Queue()
        pa_t = threading.Thread(target=self.read_output, args=(pal_client_process.stdout, q))
        pb_t = None
        pa_t.daemon = True
        pa_t.start()

        # stdout, stderr = pal_client_process.communicate()
        agent_thread = None
        current_state = State.INIT_PAL
        tournament_in_progress = True
        games = ["../available_tests/hg_nonov.json",
                 "../available_tests/hg_nonov.json",
                 "../available_tests/hg_nonov.json",
                 "../available_tests/hg_nonov.json",
                 "../available_tests/hg_nonov.json",
                 ]
        agent_started = False
        tm_thread = None
        tm_lock = threading.Lock()
        last_line = ""
        game_index = 0

        while tournament_in_progress:
            # grab the console output of PAL
            # next_line = stdout.readline()
            next_line = ""

            # while True:
            # line = q.get()
            # if line[0] == 'x':
            #     break
            # if line[0] == '2':  # stderr
            #     sys.stdout.write("\033[0;31m")  # ANSI red color
            # sys.stdout.write(line[1:])
            # next_line = line[1:]
            # if line[0] == '2':
            #     sys.stdout.write("\033[0m")  # reset ANSI code
            # sys.stdout.flush()

            # write output from procedure A (if there is any)
            try:
                next_line = q.get(False, timeout=0.1)
                sys.stdout.write("PAL: ")
                sys.stdout.write(str(next_line) + "\n")
            except queue.Empty:
                pass

            # write output from procedure B (if there is any)
            try:
                l = q2.get(False, timeout=0.1)
                # if len(l) > 3:
                sys.stdout.write("AGENT: ")
                sys.stdout.write(str(l))
            except queue.Empty:
                pass

            # if len(log_pal.readlines()) > 0:
            #     for line in log_pal.readlines():
            #         next_line = line
            #     # next_line = log_pal.readlines()[-1]
            # else:
            #     next_line = ""

            # where = log_pal.tell()
            # next_line = log_pal.readlines()[-1]
            # if not next_line:
            #     log_pal.seek(where)
            #     if "3516579813486" not in last_line:
            #         log_pal.write("3516579813486\n")
            # last_line = next_line

            # first check if we crashed or something... hopefully  this doesn't happen
            pal_client_process.poll()
            # if next_line == '' and pal_client_process.poll() is not None:
            #     break
            if agent_started:
                agent.poll()
                if agent.returncode is not None:
                    break
            if pal_client_process.returncode is not None:
                break
            # if len(str(next_line)) > 3:
            #     # print for debugging
            #     # sys.stdout.write(str(next_line) + '\n')
            #     print(next_line)
            # sys.stdout.flush()
            # next_line = ""
            # check if the tournament is over
            if game_index == len(games):
                # TODO: TOURNAMENT IS OVER. Do something?
                tournament_in_progress = False
            # wait for PAL to finish initializing. Then call to initialize a game
            if current_state == State.INIT_PAL:
                if "Minecraft finished loading" in str(next_line):
                    # MInecraft has loaded and we can run the start command. First start up our thread
                    tm_thread = TournamentManager.TournamentThread(queue=queue.Queue(), tm_lock=tm_lock)
                    tm_thread.start()
                    tm_thread.queue.put("START")
                    current_state = State.INIT_GAME
            elif current_state == State.INIT_GAME:
                if "Player" in str(next_line) and " joined the game" in str(next_line):
                    tm_thread.queue.put("RESET domain " + games[game_index])
                    current_state = State.WAIT_FOR_GAME_READY
            elif current_state == State.WAIT_FOR_GAME_READY:
                if "game initialization completed" in str(next_line):
                    current_state = State.INIT_AGENT
            elif current_state == State.INIT_AGENT:
                # TODO: initialize AI Agent?
                # agent_thread = testThread.TestThread(command="python hg_agent.py")
                # agent_thread.start()
                print("Initializing Agent Thread: python hg_agent.py")
                # subprocess.run("python hg_agent.py", shell=False)

                agent = subprocess.Popen("py hg_agent.py", shell=True, stdout=subprocess.PIPE,
                                         stdin=subprocess.PIPE)
                pb_t = threading.Thread(target=self.read_output, args=(agent.stdout, q2))
                agent_started = True
                pb_t.daemon = True
                pb_t.start()

                # stdout, stderr = agent.communicate()
                current_state = State.GAME_LOOP
            elif current_state == State.GAME_LOOP:
                # check if the game has ended somehow (stepcost, max reward, max runtime, agent gave up, game ended)
                if self.check_ended(str(next_line)):
                    # TODO: do some reporting here
                    game_index += 1
                    if game_index == len(games):
                        tournament_in_progress = False
                        break
                    else:
                        current_state = State.TRIGGER_RESET
                self.analyze_line(next_line)
            elif current_state == State.TRIGGER_RESET:
                self.commands_sent = 0
                tm_thread.queue.put("RESET domain " + games[game_index])
                current_state = State.DETECT_RESET
            elif current_state == State.DETECT_RESET:
                if "game initialization completed" in str(next_line):
                    current_state = State.GAME_LOOP
        output = pal_client_process.communicate()[0]
        exitCode = pal_client_process.returncode

        if (exitCode == 0):
            return output
        else:
            raise subprocess.CalledProcessError(exitCode, "")




class State(Enum):
    INIT_PAL = 0
    INIT_GAME = 1
    CLEANUP = 2
    INIT_AGENT = 4
    GAME_LOOP = 5
    WAIT_FOR_GAME_READY = 6
    TEST = 7,
    TRIGGER_RESET = 8
    DETECT_RESET = 9

if __name__ == "__main__":
    pal = LaunchTournament()
    pal.execute()
