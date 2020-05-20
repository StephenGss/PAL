import subprocess, threading, socket
import sys, os, signal
from PolycraftAIGym import TournamentManager
from PolycraftAIGym import PalMessenger
import testThread
from pathlib import Path
import queue
import time
from enum import Enum
import json
import PolycraftAIGym.config as CONFIG
from subprocess import PIPE
import re


class LaunchTournament:
    def __init__(self, os='Win', log_dir='Logs/', args=(), kwargs=None):
        self.commands_sent = 0
        self.total_step_cost = 0
        self.start_time = time.time()
        self.games = CONFIG.GAMES
        self.SYS_FLAG = os  # Change behavior based on SYS FLAG when executing gradlew
        if 'MACOS' in self.SYS_FLAG.upper() or 'UNIX' in self.SYS_FLAG.upper():
            self.agent_process_cmd = CONFIG.AGENT_COMMAND_UNIX
            self.pal_process_cmd = CONFIG.PAL_COMMAND_UNIX
        else:
            self.agent_process_cmd = CONFIG.AGENT_COMMAND
            self.pal_process_cmd = CONFIG.PAL_COMMAND

        ##Logging
        # self.log_port_activity = True
        log_port_file = Path(log_dir) / "port_log_{}".format(PalMessenger.PalMessenger.time_now_str())
        log_debug_file = Path(log_dir) / "debug_log_{}".format(PalMessenger.PalMessenger.time_now_str())
        # log_port_file = Path(log_dir) / "port_log.txt"  # This file won't be used; see issue_reset()
        sent_print_bool = False          # PAL commands are short enough to put in the console
        sent_log_write_bool = True      # Log everything sent to the port
        recd_print_bool = False         # PAL responses are often long and ungainly; no need to print them
        recd_log_write_bool = True      # Log everything that comes from the port
        debug_print_bool = True         # For useful stuff, send it to the console
        debug_log_write_bool = True    # No need to keep it though
        # junk_print_bool = False         # For not useful stuff, retain the option to change my mind
        # junk_log_write_bool = False     # No need to keep it though
        # # I recognize that some utility like logging may be better, but whatever:
        self.agent_log = PalMessenger.PalMessenger(sent_print_bool, sent_log_write_bool, log_port_file, log_note="AGENT: ")
        self.PAL_log = PalMessenger.PalMessenger(recd_print_bool, recd_log_write_bool, log_port_file, log_note="PAL: ")
        # self.junk_log = PalMessenger(junk_print_bool, junk_log_write_bool, log_note="JUNK: ")
        self.debug_log = PalMessenger.PalMessenger(debug_print_bool, debug_log_write_bool, log_debug_file,  log_note="DEBUG: ")


        ## Tournament Data
        self.agent = None
        self.q = queue.Queue()
        self.q2 = queue.Queue()
        self.pa_t = None
        self.pb_t = None
        self.tm_thread = None
        self.tm_lock = threading.Lock()
        self.game_index = 0

        # stdout, stderr = pal_client_process.communicate()
        agent_thread = None
        self.pal_client_process = None
        self.current_state = State.INIT_PAL
        self.tournament_in_progress = True

        self.agent_started = False

    @DeprecationWarning
    def analyze_line(self, line):
        """
        WHat is this supposed to do? Reporting Purposes?
        :param line:
        :return:
        """
        return None

    def check_ended(self, line):
        # NoTODO: Track stepcost to call reset -- completed
        # TODO: Track total reward to call reset. Not for dry-run
        # NoTODO: Track total run time to call reset -- completed
        # TODO: Track agent giveup to call reset
        # NoTODO: Track end condition flag to call reset -- completed
        self.commands_sent += 1

        # steps greater than 60, END
        line_end_str = '\\r\\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\\n'
        if line.find('{') != -1 and line.find(line_end_str) != -1:
            json_text = line[line.find('{'):line.find(line_end_str)]  # Make this system agnostic - previously \\r\\n
            # TODO: Potentially remove this?
            json_text = re.sub(r'\\\\\"', '\'', json_text)
            data_dict = json.loads(json_text)

            self.total_step_cost += data_dict["command_result"]["stepCost"]

            if data_dict["goal"]["goalAchieved"]:
                self.debug_log.message("Game Over: Goal Achieved")
                return True
            if self.total_step_cost > CONFIG.MAX_STEP_COST:
                self.debug_log.message("Game Over: total step cost exceeded limit")
                return True
            if (time.time() - self.start_time) > CONFIG.MAX_TIME:
                self.debug_log.message("Game Over: time exceeded limit")
                return True
            # if self.commands_sent > 10000:
            #     return True

        return None

    def read_output(self, pipe, q):
        """reads output from `pipe`, when line has been read, puts
    line on Queue `q`"""
        while True and not pipe.closed:
            l = pipe.readline()
            q.put(l)

    def _check_queues(self):
        next_line = ""

        # write output from procedure A (if there is any)
        try:
            next_line = self.q.get(False, timeout=0.1)
            self.PAL_log.message(str(next_line))
            # sys.stdout.write("PAL: ")
            # sys.stdout.write(str(next_line) + "\n")
            # sys.stdout.flush()
        except queue.Empty:
            pass

        # write output from procedure B (if there is any)
        try:
            l = self.q2.get(False, timeout=0.1)
            # if len(l) > 3:
            self.agent_log.message(str(l))
            # sys.stdout.write("AGENT: ")
            # sys.stdout.write(str(l))
            # sys.stdout.flush()
        except queue.Empty:
            pass

        return next_line

    def execute(self):
        processes = []
        # pal_client_process = subprocess.Popen(command, shell=True, cwd='../', stdout=subprocess.PIPE)

        # log_pal = open('pal_log.txt', 'w+')
        # Launch Minecraft Client
        self.pal_client_process = subprocess.Popen(self.pal_process_cmd, shell=True, cwd='../', stdout=subprocess.PIPE,
                                                   stdin=subprocess.PIPE)
        self.pa_t = threading.Thread(target=self.read_output, args=(self.pal_client_process.stdout, self.q))
        self.pa_t.daemon = True
        self.pa_t.start()  # Kickoff the PAL Minecraft Client
        self.debug_log.message("PAL Client Initiated")

        while self.tournament_in_progress:
            # grab the console output of PAL
            # next_line = stdout.readline()

            next_line = self._check_queues()

            # first check if we crashed or something... hopefully  this doesn't happen
            self.pal_client_process.poll()
            # if next_line == '' and pal_client_process.poll() is not None:
            #     break
            if self.agent_started:
                self.agent.poll()
                if self.agent.returncode is not None:
                    break
            if self.pal_client_process.returncode is not None:
                break

            # wait for PAL to finish initializing. Then call to initialize a game
            if self.current_state == State.INIT_PAL:
                if "Minecraft finished loading" in str(next_line):
                    # MInecraft has loaded and we can run the start command. First start up our thread
                    self._launch_tournament_manager()
                    self.current_state = State.LAUNCH_TOURNAMENT

            # Wait for player to join launched tournament
            elif self.current_state == State.LAUNCH_TOURNAMENT:
                if "[Server thread/INFO]: Player" in str(next_line) and " joined the game" in str(next_line):
                    self.tm_thread.queue.put("LAUNCH domain " + self.games[self.game_index])
                    self.debug_log.message("LAUNCH domain command issued")
                    self.start_time = time.time()
                    self.current_state = State.WAIT_FOR_GAME_READY

            # Wait for all entities to load
            elif self.current_state == State.WAIT_FOR_GAME_READY:
                if "[EXP] game initialization completed" in str(next_line):
                    self.debug_log.message("Game Initialized. ")
                    self.current_state = State.INIT_AGENT

            # Launch the AI agent and start the experiment
            elif self.current_state == State.INIT_AGENT:
                self._launch_ai_agent()
                self.current_state = State.GAME_LOOP

            # Begin the Game Loop
            elif self.current_state == State.GAME_LOOP:
                # check if the game has ended somehow (stepcost, max reward, max runtime, agent gave up, game ended)
                if self.check_ended(str(next_line)):
                    # TODO: do some reporting here
                    self.debug_log.message("Game has ended.")
                    self._game_over()

                    # Check if the tournament is over
                    if self.game_index >= len(self.games):
                        self._tournament_completed()
                        break
                    else:
                        self.current_state = State.TRIGGER_RESET
                # self.analyze_line(next_line)

            # Reset the Tournament for the next game
            elif self.current_state == State.TRIGGER_RESET:
                self.debug_log.message("Reset Triggered... ")
                self._trigger_reset()

                self.current_state = State.DETECT_RESET

            # Wait for reset to complete; then reset the game loop
            elif self.current_state == State.DETECT_RESET:
                if "[EXP] game initialization completed" in str(next_line):
                    self.debug_log.message("Reset Complete. Switching to Game Loop... ")
                    self.current_state = State.GAME_LOOP

        output = self.pal_client_process.communicate()[0]
        exitCode = self.pal_client_process.returncode

        if (exitCode == 0):
            return output
        else:
            raise subprocess.CalledProcessError(exitCode, "")

    def _launch_tournament_manager(self):
        self.tm_thread = TournamentManager.TournamentThread(queue=queue.Queue(), tm_lock=self.tm_lock)
        self.tm_thread.start()
        self.tm_thread.queue.put("START")
        self.debug_log.message('Started Tournament')

    def _launch_ai_agent(self):
        print("Initializing Agent Thread: python hg_agent.py")
        # subprocess.run("python hg_agent.py", shell=False)
        # TODO: Replace the AI Agent Subprocess here if needed...

        self.agent = subprocess.Popen(self.agent_process_cmd, shell=True, stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE)
        self.pb_t = threading.Thread(target=self.read_output, args=(self.agent.stdout, self.q2))
        self.agent_started = True
        self.pb_t.daemon = True
        self.pb_t.start()
        self.debug_log.message("Launched AI Agent")

    def _game_over(self):
        self.debug_log.message("Completed game " + str(self.game_index))
        sys.stdout.flush()
        self.game_index += 1


    def _tournament_completed(self):
        self.debug_log.message("Tournament Completed: " + str(len(self.games)) + "games run")
        sys.stdout.flush()
        os.kill(self.agent.pid, signal.SIGTERM)
        os.kill(self.pal_client_process.pid, signal.SIGTERM)
        self.tm_thread.join()
        self.tournament_in_progress = False

    def _trigger_reset(self):
        self.commands_sent = 0
        self.total_step_cost = 9
        self.start_time = time.time()
        self.tm_thread.queue.put("RESET domain " + self.games[self.game_index])
        self.debug_log.message("RESET domain command sent to tm_thread.")

class State(Enum):
    INIT_PAL = 0
    LAUNCH_TOURNAMENT = 1
    CLEANUP = 2
    INIT_AGENT = 4
    GAME_LOOP = 5
    WAIT_FOR_GAME_READY = 6
    TEST = 7
    TRIGGER_RESET = 8
    DETECT_RESET = 9

if __name__ == "__main__":
    pal = LaunchTournament('MACOS')
    pal.execute()