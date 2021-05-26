import subprocess, threading
import sys, os
import TournamentManager, PalMessenger, AzureConnectionService
from pathlib import Path
import queue
import time, datetime
from enum import Enum
import json
import config as CONFIG
from subprocess import PIPE
import re
from collections import defaultdict
from copy import copy, deepcopy
import getopt
import psutil
from spython.main import Client as sClient


class LaunchTournament:
    """
    Manages the running of a single AI Agent + Single MC Client through various "Games"
    The Tournament Config is found in config.py and describes:
        - Agent AI Python Script
        - Game End conditions (Max time, max step cost (running total)
        - List of games that are a part of this tournament

    As UNIX differs from Windows in executing scripts, the "os=" input is used to determine which system this is
    If you are running a unix-based machine, please pass in "MACOS" or "UNIX" (they do the same thing).

    All messages in stdout for the AI Agent, PAL client, and Debugging are written to log files (see logging below)
    """
    def __init__(self, os='Unix', log_dir='Logs/', args=(), kwargs=None):
        self.commands_sent = 0
        self.total_step_cost = 0
        self.start_time = time.time()
        self.tournament_start_time = datetime.datetime.now()
        self.log_dir = CONFIG.LOG_DIR + f"{PalMessenger.PalMessenger.time_now_str('_')}/"
        self.SYS_FLAG = os  # Change behavior based on SYS FLAG when executing gradlew
        self.temp_logs_path = "log_file_paths.txt"
        self.sql_err_log_path = CONFIG.SQL_ERR_LOG_DIR
        # TODO: do we need this? removed for Europa
        # self.lock = FileLock(f"{self.temp_logs_path}.lock")  # Lock file for all log files

        # TODO: use os library to detect this vs. passing in as a command line argument.
        if 'MACOS' in self.SYS_FLAG.upper() or 'UNIX' in self.SYS_FLAG.upper():
            self.agent_process_cmd = CONFIG.AGENT_COMMAND_UNIX
            self.pal_process_cmd = CONFIG.PAL_COMMAND_UNIX
        else:
            self.agent_process_cmd = CONFIG.AGENT_COMMAND
            self.pal_process_cmd = CONFIG.PAL_COMMAND

        ## Tournament Data
        self.agent = None
        self.agent_reader = None
        self.PAL_reader = None
        self.q = queue.Queue()
        self.q2 = queue.Queue()
        self.pa_t = None
        self.pb_t = None
        self.tm_thread = None
        self.end_event = threading.Event()
        self.tm_lock = threading.Lock()
        self.game_index = 0

        # stdout, stderr = pal_client_process.communicate()
        agent_thread = None
        self.pal_client_process = None
        self.current_state = State.INIT_PAL
        self.tournament_in_progress = True
        self.agent_started = False
        self.upload_thread = None
        self.upload_thread_running = False

        ## Results
        self.score_dict = {}
        self.game_score_dict = defaultdict(lambda: defaultdict(lambda: 0))
        self.threads = None

        ##Logging
        self._create_logs()

        ## Monitoring
        self.wait_for_gameover_timer = None
        self.wait_for_nextgame_init_timer = None
        self.next_game_initialized_flag = False
        self.restart_PAL_counter = 0

        ## Screen
        self.vdisplay = None

        #Load Games
        self.games = self._build_game_list(CONFIG.GAME_COUNT)

    def _build_game_list(self, ct):
        """
        Given a folder containing all games for a tournament, walks through the folder and adds
        all of the .json files to the list of files to be read.

        As games must be played in the right order, this function uses a helper script to sort the games in the right order

        Note: the .json2 files with the same name must also be in this folder!
        :param ct: Maximum games to be run. if Count > #games available in a folder, the maximum number of available games are played
        :return: a sorted list containing all games to be played in this tournament
        """
        file_type = '.json'
        file_list = []
        rootdir = CONFIG.GAMES_FOLDER  # Set this either in config.py or by passing in the -g CLI parameter.
        for subdir, dirs, files in os.walk(rootdir):
            for file in files:
                filepath = subdir + '/' + file
                if filepath.endswith(file_type):
                    file_list.append(filepath)

        self.debug_log.message(f"Game List created. {len(file_list)} games read. {len(file_list[:ct])} games will be played")
        if ct <= 0:
            sorted_files = self._sort_files(file_list)
        else:
            sorted_files = self._sort_files(file_list)[:ct]

        self.debug_log.message(f"sorted games to be played: {sorted_files}")
        return sorted_files

    def _sort_files(self, files):
        """
        (static) Helper Script that sorts the JSON games in a tournament folder. Note that this searches for the pattern
            '_Gxxxx_'
        in the file names of the jsons (where x's are digits between 0 & 9 and represent the Game Number of the game),
        and sorts them from least to greatest.

        All pre-generated tournaments are named with the right pattern.
        Note that the file path containing this folder cannot contain _Gxxxx_ in its name, as that will cause issues.

        :param files: list of files to be sorted
        :return: a sorted list of files by Game Number
        :raise: ValueError if _Gxxxx_ is not found in the file names.
        """
        sorted_dict = {}
        for file in files:
            values = re.search("_G(\d+)_", file)
            if not values:
                raise ValueError("Error - files are not named correctly! " + file)
            sorted_dict[int(values.groups()[0])] = file

        sorted_file_list = []
        for i in sorted(sorted_dict.keys()):
            sorted_file_list.append(sorted_dict[i])

        return sorted_file_list

    def _create_logs(self):
        """
        Creates the log file handlers
        Re-run after each game to create a new log file
        """
        log_dir = self.log_dir
        log_port_file = Path(log_dir) / f"PAL_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str('_')}.txt"
        agent_port_file = Path(log_dir) / f"Agent_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str('_')}.txt"
        log_debug_file = Path(log_dir) / f"Debug_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str('_')}.txt"
        log_speed_file = Path(log_dir) / f"speed_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str('_')}.txt"

        # To see logs written to STDOUT of the Main Thread, change *_print to True.
        should_agent_print = False      # should Agent STDOUT print to main thread STDOUT (default: False)
        should_agent_write_log = True   # should Agent STDOUT write to an Agent Log? (Default: True)
        should_PAL_print = False        # should PAL STDOUT print to main thread STDOUT (default: False)
        should_PAL_write_log = True     # should PAL STDOUT write to a PAL log? (default: True)
        should_debug_print = True       # send useful progress updates to main thread STDOUT (default: True)
        should_debug_write_log = True   # write useful debug log updates to a Debug log (default: True)
        speed_print_bool = True         # Speed Log outputs Steps Per Second to log
        speed_log_write_bool = True     # Speed Log writes Steps per second to File

        # # I recognize that some utility like logging may be better, but whatever:
        self.agent_log = PalMessenger.PalMessenger(should_agent_print, should_agent_write_log, agent_port_file,
                                                   log_note="AGENT: ")
        self.PAL_log = PalMessenger.PalMessenger(should_PAL_print, should_PAL_write_log, log_port_file, log_note="PAL: ")

        self.debug_log = PalMessenger.PalMessenger(should_debug_print, should_debug_write_log, log_debug_file,
                                                   log_note="DEBUG: ")
        self.speed_log = PalMessenger.PalMessenger(speed_print_bool, speed_log_write_bool, log_speed_file,
                                                   log_note="FPS: ")

    def _check_ended(self, line):
        """
        Check the stdout to see if game ending conditions are met
        :param line: Current Line in the STDOUT of either PAL or AGENT threads
        :return: True if the game has ended.
        """
        # TODO: Track total reward to call reset. Not for dry-run

        line_end_str = '\r\n'
        line_end_str = '\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\n'

        # Agent Giveup check:
        if line.find('[AGENT]GIVE_UP') != -1:
            msg = 'Agent Gives Up'
            self.debug_log.message(f"Game Over: {msg}")
            self.score_dict[self.game_index]['success'] = 'False'
            self.score_dict[self.game_index]['success_detail'] = msg
            return True

        if line.find('{') != -1 and line.find(line_end_str) != -1 and line.rfind('}') != -1:
            json_text = line[line.find('{'):line.rfind('}')+1]
            # TODO: Potentially remove this?
            json_text = re.sub(r'\\\\\"', '\'', json_text)
            json_text = re.sub(r'\\+\'', '\'', json_text)
            data_dict = json.loads(json_text)
            self.commands_sent += 1
            self.total_step_cost += data_dict["command_result"]["stepCost"]

            if data_dict["goal"]["goalAchieved"]:
                msg = 'Goal Achieved'
                self.debug_log.message(f"Game Over: {msg}")
                self.score_dict[self.game_index]['success'] = 'True'
                self.score_dict[self.game_index]['success_detail'] = msg
                return True
            if self.total_step_cost > CONFIG.MAX_STEP_COST:
                msg = "total step cost exceeded limit"
                self.debug_log.message(f"Game Over: {msg}")
                self.score_dict[self.game_index]['success'] = 'False'
                self.score_dict[self.game_index]['success_detail'] = msg
                return True

        # Check If Game Timed out.
        self.score_dict[self.game_index].update({'elapsed_time': time.time() - self.start_time})
        if self.score_dict[self.game_index]['elapsed_time'] > CONFIG.MAX_TIME:
            msg = 'time exceeded limit'
            self.debug_log.message(f"Game Over: {msg}")
            self.score_dict[self.game_index]['success'] = 'False'
            self.score_dict[self.game_index]['success_detail'] = msg
            return True
        
        return None


    def read_output(self, pipe, q, timeout=1):
        """
        This is run on a separate daemon thread for both PAL and the AI Agent.

        This takes the STDOUT (and STDERR that gets piped to STDOUT from the Subprocess.POpen() command)
        and places it into a Queue object accessible by the main thread
        """
        # read both stdout and stderr

        flag_continue = True
        while flag_continue and not pipe.stdout.closed:
            try:
                l = pipe.stdout.readline()
                q.put(l)
                sys.stdout.flush()
                pipe.stdout.flush()
            except UnicodeDecodeError as e:
                print(f"Err: UnicodeDecodeError: {e}")
                try:
                    l = pipe.stdout.read().decode("utf-8")
                    q.put(l)
                    sys.stdout.flush()
                    pipe.stdout.flush()
                except Exception as e2:
                    print(f"ERROR - CANT HANDLE OUTPUT ENCODING! {e2}")
                    sys.stdout.flush()
                    pipe.stdout.flush()
            except Exception as e3:
                print(f"ERROR - UNKNOWN EXCEPTION! {e3}")
                sys.stdout.flush()
                pipe.stdout.flush()

    def _check_queues(self, check_all=False):
        """
        Check the STDOUT queues in both the PAL and Agent threads, logging the responses appropriately
        :return: next_line containing the STDOUT of the PAL process only:
                    used to determine game ending conditions and update the score_dict{}
        """
        next_line = ""

        # # write output from procedure A (if there is any)
        # DN: Remove "blockInFront" data from PAL, as it just gunks up our PAL logs for no good reason.
        try:
            next_line = self.q.get(False, timeout=0.025)
            self.PAL_log.message_strip(str(next_line))
            sys.stdout.flush()
            sys.stderr.flush()
        except queue.Empty:
            pass

        # write output from procedure B (if there is any)
        try:
            if check_all:
                while not self.q2.empty():
                    l = self.q2.get(False, timeout=0.025)
                    if len(str(l)) > 1:
                        self.agent_log.message(str(l))
                    sys.stdout.flush()
                    sys.stderr.flush()
            else:
                l = self.q2.get(False, timeout=0.025)
                self.agent_log.message(str(l))
                sys.stdout.flush()
                sys.stderr.flush()

        except queue.Empty:
            pass

        # Handles edge case where this msg comes sooner than anticipated.
        if "[EXP] game initialization completed" in str(next_line):
            self.next_game_initialized_flag = True

        return next_line

    def execute(self):
        """
        Main Tournament Loop

        Tracks the Current State of the tournament, launching Threads and Passing Commands to the Tournament Manager.
        :return:
        """

        # override launch command for Europa
        if 'SINGULARITYENV_PAL_TM_PORT' in os.environ:
            agent_port = os.environ['SINGULARITYENV_PAL_PORT']
            tm_port = os.environ['SINGULARITYENV_PAL_TM_PORT']
            self.pal_process_cmd = str(self.pal_process_cmd).replace('9000:9000/tcp', agent_port + ':9000/tcp')
            self.pal_process_cmd = str(self.pal_process_cmd).replace('9005:9005/tcp', tm_port + ':9005/tcp')
            print('Using Ports: Agent:' + os.environ['SINGULARITYENV_PAL_PORT'] + '|| TM:' + os.environ['SINGULARITYENV_PAL_TM_PORT'])

        # Launch Minecraft Client
        self.debug_log.message("PAL command: " + self.pal_process_cmd)
        # self.vdisplay = Xvfb(width=1280, height=740)
        # self.vdisplay.start()

        self.pal_client_process = subprocess.Popen(self.pal_process_cmd, shell=True, cwd='../', stdout=subprocess.PIPE,
                                                   # stdin=subprocess.PIPE,  # DN: 0606 Removed for perforamnce
                                                   stderr=subprocess.STDOUT, # DN: 0606 - pipe stderr to STDOUT. added for performance
                                                   bufsize=1,                # DN: 0606 Added for buffer issues
                                                   universal_newlines=True,  # DN: 0606 Added for performance - needed for bufsize=1 based on docs?
                                                   )

        self.pa_t = threading.Thread(target=self.read_output, args=(self.pal_client_process, self.q))
        self.pa_t.daemon = True
        self.pa_t.start()  # Kickoff the PAL Minecraft Client
        self.debug_log.message("PAL Client Initiated")

        while self.tournament_in_progress:
            # time.sleep(0.0001)
            # grab the console output of PAL
            next_line = self._check_queues(check_all=True)

            # first check if we crashed or something... hopefully  this doesn't happen
            self.pal_client_process.poll()

            if self.agent_started:
                self.agent.poll()
                if self.agent.returncode is not None:
                    self.debug_log.message(f"ERROR: Agent THREAD CRASHED WITH CODE: {self.agent.returncode}")
                    break
                # If agent started & PAL crashes, kill the main thread.
                if self.pal_client_process.returncode is not None:
                    self.debug_log.message(f"ERROR: PAL THREAD CRASHED WITH CODE: {self.pal_client_process.returncode}")
                    break

                # If upload thread has stopped prematurely, then there is cause for concern.
                if self.upload_thread_running and self.upload_thread is not None and not self.upload_thread.is_alive():
                    self.debug_log.message(f"Alert: Upload Thread has ended. Tournament Complete or Agent thread has hung")
                    # self._game_over()
                    self._tournament_completed()
                    # self.tournament_in_progress = False  # force this because it seems to not be happening on Europa??
                    break
            # If agent hasn't started yet but PAL crashes, re-start PAL.
            elif self.pal_client_process.returncode is not None:
                if self.current_state == State.INIT_PAL and self.restart_PAL_counter < 10:
                    self.restart_PAL_counter += 1
                    self.q = queue.Queue()  # Re-initialize the q object & ignore crashed data.
                    self.pal_client_process = subprocess.Popen(self.pal_process_cmd, shell=True, cwd='../',
                                                               stdout=subprocess.PIPE,
                                                               # stdin=subprocess.PIPE,  # DN: 0606 Removed for perforamnce
                                                               stderr=subprocess.STDOUT,
                                                               bufsize=1,  # DN: 0606 Added for buffer issues
                                                               universal_newlines=True,
                                                               # DN: 0606 Added for performance - needed for bufsize=1 based on docs?
                                                               )

                    self.pa_t = threading.Thread(target=self.read_output, args=(self.pal_client_process, self.q))
                    self.pa_t.daemon = True
                    self.pa_t.start()  # Kickoff the PAL Minecraft Client
                    self.debug_log.message("PAL Client ERROR. PAL Client Re-Initialized...")
                else:
                    self.debug_log.message("PAL Client ERROR. Game State Misalignment. Tournament Ending. What happened?")
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
                    self._setup_next_game()
                    self.current_state = State.WAIT_FOR_GAME_READY

            # Wait for all entities to load
            elif self.current_state == State.WAIT_FOR_GAME_READY:
                if "[EXP] game initialization completed" in str(next_line):
                    self.debug_log.message("Game Initialized. ")
                    self.current_state = State.INIT_AGENT
                    self.next_game_initialized_flag = False

            # Launch the AI agent and start the experiment
            elif self.current_state == State.INIT_AGENT:
                self._launch_ai_agent()
                self.current_state = State.WAIT_FOR_AGENT_START

            elif self.current_state == State.WAIT_FOR_AGENT_START:
                if self._check_agent_cmd(str(next_line)):
                    self.debug_log.message("Agent Ready - Game Starting")
                    # Start the game time now:
                    self.start_time = time.time()  # Start Time at this point.
                    self.score_dict[self.game_index]['startTime'] = PalMessenger.PalMessenger.time_now_str()
                    self.current_state = State.GAME_LOOP

                    # Initialize Uploading Thread
                    # FIXME: Change how we do this for Europa
                    self.upload_thread = threading.Thread(name="update_logs_thread",
                                                          target=self._launch_interval_update_results_table)
                    self.upload_thread.daemon = True
                    self.upload_thread.start()

            # Begin the Game Loop
            elif self.current_state == State.GAME_LOOP:

                # Update the score_dict
                self._record_score(str(next_line))
                self._check_novelty(str(next_line))

                # check if the game has ended somehow (stepcost, max reward, max runtime, agent gave up, game ended)
                if self._check_ended(str(next_line)):

                    next_game_idx = self.game_index + 1
                    # Check if the tournament is over
                    if next_game_idx >= len(self.games) or (self.tournament_start_time + datetime.timedelta(minutes=CONFIG.MAX_TOURN_TIME)) <= datetime.datetime.now():
                        if (self.tournament_start_time + datetime.timedelta(minutes=CONFIG.MAX_TOURN_TIME)) <= datetime.datetime.now():
                            self.debug_log.message("Max tournament time exceeded: " + str(CONFIG.MAX_TOURN_TIME) + " minutes")
                        # If so, end the game now (don't wait for gameover True)
                        self.debug_log.message("Game has ended.")
                        self.speed_log.message(
                            str(self.game_index) + ": " + str(self.commands_sent / (time.time() - self.start_time)))
                        self._game_over()
                        self._tournament_completed()
                        break
                    else:
                        # Send next game to agent
                        self.current_state = State.WAIT_FOR_GAMEOVER_TRUE
                        self._reset_and_flush()
                        self.wait_for_gameover_timer = time.time()
                        # Wait for GameOver == True to be sent to the Client before switching the log files.
                        self.debug_log.message("Waiting for Gameover True")

            # Game completed. Wait for Agent to also get the message that game is over before sending logs.
            elif self.current_state == State.WAIT_FOR_GAMEOVER_TRUE:
                #TODO: adjust this hang time if necessary
                MAX_HANG_TIME = 6  # seconds - based on avg ~ 0.25 actions/second + 1 second buffer
                # Don't record any more scores! Game already completed.
                # self._record_score(str(next_line))
                move_on = self._gameover_passed_to_agent(str(next_line))
                if move_on or (time.time() - self.wait_for_gameover_timer) > MAX_HANG_TIME:
                    if not move_on:
                        self.debug_log.message("WARN: gameover message likely missed? Moving to Next Game...")
                    self.debug_log.message("Game has ended.")
                    self.speed_log.message(
                        str(self.game_index) + ": " + str(self.commands_sent / (time.time() - self.start_time)))
                    self._game_over()

                    # # Check if the tournament is over
                    # if self.game_index >= len(self.games):
                    #     self._tournament_completed()
                    #     break
                    # else:
                        # If the game is over, trigger a reset and load the next game.
                    self.current_state = State.TRIGGER_RESET

            # Reset the Tournament for the next game
            elif self.current_state == State.TRIGGER_RESET:
                self.debug_log.message("Reset Triggered... ")
                self._trigger_reset()

                self.current_state = State.DETECT_RESET
                sys.stdout.flush()
                sys.stderr.flush()
                # self.wait_for_nextgame_init_timer = time.time()

            # Wait for reset to complete; then reset the game loop
            elif self.current_state == State.DETECT_RESET:
                sys.stdout.flush()
                sys.stderr.flush()
                # Typical Scenario: below text shows up after the reset is triggered.
                # However, case exists where messages may come faster than we can process
                # New solution: Look for this line and set a global flag in the _check_queues() function

                if "[EXP] game initialization completed" in str(next_line):
                    self.debug_log.message("Reset Complete. Switching to Game Loop... ")
                    self.current_state = State.GAME_LOOP
                    self.start_time = time.time() # Start Time at this point.
                    self.score_dict[self.game_index]['startTime'] = PalMessenger.PalMessenger.time_now_str()
                    self.next_game_initialized_flag = False


        #output = self.pal_client_process.communicate()[0]
        exitCode = self.pal_client_process.returncode

        # TODO: Safe to remove? Not sure how this is helpful.
        if exitCode == 0:
            print("Tournament Completed -ExitCode 0")
            return
        elif exitCode is None:
            self._tournament_completed() # FixMe: is this needed?
            print("ERROR: tournament incomplete - critical thread failure during execution. Agent Hung?")
            return
        else:
            print(f"ERROR: ExitCode: {exitCode}")
            self._tournament_completed() # FixMe: is this needed?
            raise subprocess.CalledProcessError(exitCode, "")

    def _launch_tournament_manager(self):
        """
        Launch the Tournament Manager Thread
        """
        self.tm_thread = TournamentManager.TournamentThread(queue=queue.Queue(), tm_lock=self.tm_lock)
        self.tm_thread.start()
        self.tm_thread.queue.put("START")
        self.debug_log.message('Started Tournament')

    def _launch_ai_agent(self):
        """
        Launch the AI agent Thread
        """
        self.debug_log.message(f"Initializing Agent Thread: {CONFIG.AGENT_COMMAND_UNIX}")

        self.agent = subprocess.Popen(self.agent_process_cmd, shell=True, cwd=CONFIG.AGENT_DIRECTORY, stdout=subprocess.PIPE,
                                      # stdin=subprocess.PIPE,      #DN: 0606 Removed for performance
                                      stderr=subprocess.STDOUT,
                                      bufsize=1,                    #DN: 0606 Added for performance
                                      universal_newlines=True,      #DN: 0606 Added for performance
                                      )
        # Launch Listening Thread to log STDOUT from the Agent.
        self.pb_t = threading.Thread(target=self.read_output, args=(self.agent, self.q2))
        self.agent_started = True
        self.pb_t.daemon = True
        self.pb_t.start()
        self.debug_log.message("Launched AI Agent")

    def _launch_interval_update_results_table(self):
        self.debug_log.message("Initializing Interval Upload Thread")
        upload_file = Path(self.log_dir) / f"{CONFIG.TOURNAMENT_ID}.txt"
        upload_log = PalMessenger.PalMessenger(True, True, upload_file, log_note="UPLOAD: ")
        azure = AzureConnectionService.AzureConnectionService(upload_log, temp_logs_err_path=self.sql_err_log_path)
        if azure.is_connected():
            self.upload_thread_running = True
            azure.threaded_update_logs(self.end_event)
        else:
            self.debug_log.message("Azure Connection Error - cannot connect to SQL database")
            # raise ConnectionError("Error - cannot update results table")

    def _game_over(self):
        """
        Game over cleanup method
        At game end, upload game logs to Blob and record scores in the SQL server

        """
        self.debug_log.message("Completed game " + str(self.game_index))
        self.debug_log.message(f"Final Score: {str(self.score_dict)}")
        sys.stdout.flush()
        self.score_dict[self.game_index]['endTime'] = PalMessenger.PalMessenger.time_now_str()

        # self.threads = self._update_azure(self.game_index)
        # azure = AzureConnectionService.AzureConnectionService(self.debug_log)
        # Pass a copy of all necessary variables to the separate thread to prevent SIGBUS faults.
        self.threads = threading.Thread(name="azure_cxn", target=self._update_azure,
                                        args=(int(self.game_index),
                                              deepcopy(self.score_dict),
                                              deepcopy(self.game_score_dict),
                                              copy(self.debug_log),
                                              copy(self.agent_log),
                                              copy(self.PAL_log),
                                              copy(self.speed_log),
                                              ))
        self.threads.start()
        self.game_index += 1
        self._create_logs()

    def _update_azure(self, game_index, score_dict, game_dict, debug_log, agent_log, PAL_log, speed_log):
        """
        Threaded function to upload all relevant data to our azure storage. Will Print Errors to STDERR
        and will print Errors to the Debug Log.

        Any errors will not cause mainThread hangups.
        """
        # self.pb_t = threading.Thread(target=self.read_output, args=(self.agent, self.q2))
        azure = AzureConnectionService.AzureConnectionService(debug_log)

        if azure.is_connected():
            azure.send_summary_to_azure(score_dict=score_dict, game_id=game_index)
            azure.send_game_details_to_azure(game_dict=game_dict, game_id=game_index)
            azure.upload_pal_messenger_logs(palMessenger=agent_log, log_type="agent", game_id=game_index)
            azure.upload_pal_messenger_logs(palMessenger=PAL_log, log_type="pal", game_id=game_index)
            azure.upload_pal_messenger_logs(palMessenger=debug_log, log_type="debug", game_id=game_index)
            # azure.upload_pal_messenger_logs(palMessenger=speed_log, log_type='speed', game_id=game_index)



    def _tournament_completed(self):
        """
        Tournament Complete - initiate cleanup of threads

        :return:
        """
        self._check_queues(check_all=True)
        self.debug_log.message("Tournament Completed: " + str(self.game_index) + "games run")
        sys.stdout.flush()
        # os.kill(self.agent.pid, signal.SIGTERM)
        # os.kill(self.pal_client_process.pid, signal.SIGTERM)
        # set end_event so we don't wait for the upload thread to restart
        self.end_event.set()

        self.tm_thread.kill()
        if self.threads is not None:
            self.threads.join()
            # for i in self.threads:
            #     i.join()
        self._kill_process_children(5)
        self.debug_log.message("Tournament Ending. Join tm_thread")
        if self.tm_thread is not None:
            self.tm_thread.join(timeout=5)
        self.debug_log.message("Tournament Ending. Join upload_thread")
        if self.upload_thread is not None:
            self.upload_thread.join()

        self.tournament_in_progress = False

        self.debug_log.message("Tournament Ending. Closing vDisplay if exists")
        if self.vdisplay is not None:
            self.vdisplay.stop()

    def _kill_process_children(self, timeout):
        """
        Helper function to kill all child processes of the main thread.
        :param timeout:
        :return:
        """
        # Kill the client process first to stop it from sending messages to the server
        # FIXME: change for Europa or get psutil on Europa
        # check for loaded singularity instances and kill them
        # self.debug_log.message("List all singularity instances: ")
        # print(str(sClient.instances()))
        # self.debug_log.message("Kill all singularity instances")
        # sClient.instance_stopall()

        procs = list(psutil.Process(os.getpid()).children(recursive=True))
        for p in procs:
            try:
                self.debug_log.message("Attempting to terminate Process: " + str(p.pid))
                p.terminate()
                self.debug_log.message("terminated Process: " + str(p.pid))
            except psutil.NoSuchProcess:
                self.debug_log.message("Failed to find Process: " + str(p.pid))
                pass
        gone, alive = psutil.wait_procs(procs, timeout=timeout)
        for p in alive:
            try:
                self.debug_log.message("Attempting to kill Process: " + str(p.pid))
                p.kill()
                self.debug_log.message("Killed Process: " + str(p.pid))
            except psutil.NoSuchProcess:
                self.debug_log.message("Failed to find Process: " + str(p.pid))
                pass

    def _reset_and_flush(self):
        """
        Call the Reset Command and send the next game to PAL.
        :return:
        """
        self.tm_thread.queue.put("RESET domain " + self.games[self.game_index + 1])
        self.debug_log.message("RESET domain command sent to tm_thread.")


    def _trigger_reset(self):
        """
        Trigger a reset in PAL - setting the stage for the next game
        :return:
        """
        self.commands_sent = 0
        self.total_step_cost = 9
        self._setup_next_game()


    def _check_novelty(self, line):
        """
        Checks to see if the agent reported that Novelty was Detected
        :param line: Current Line in STDOUT
        """
        line_end_str = '\r\n'
        line_end_str = '\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\n'
        if line.find('REPORT_NOVELTY') != -1 and line.find(line_end_str) != -1:
            self.score_dict[self.game_index]['noveltyDetect'] = 1
            self.score_dict[self.game_index]['noveltyDetectStep'] = self.score_dict[self.game_index]['step']
            self.score_dict[self.game_index]['noveltyDetectTime'] = PalMessenger.PalMessenger.time_now_str()

    def _record_score(self, line):
        """
        Checks to see if the current line contains a score update provided by PAL and keeps track of it if so
        :param line: Current Line in STDOUT

        Example Result String from [CLIENT]
        {"goal":{"goalType":"BLOCK_TO_LOCATION","goalAchieved":false},
        "command_result":{"command":"smooth_move","argument":"w","result":"SUCCESS","message":"","stepCost":27.906975},
        "step":1,
        "gameOver":false}\n'
        """
        line_end_str = '\r\n'
        line_end_str = '\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\n'

        # Case 1: Record a Response from PAL to an Agent Command
        if line.find('[CLIENT]{') != -1 and line.find(line_end_str) != -1 and line.rfind('}') != -1:
            # Get timestamp:
            json_text = line[line.find('{'):line.rfind('}')+1]
            # json_text = line[line.find('{'):line.find(line_end_str)]

            json_text = re.sub(r'\\\\\"', '\'', json_text)
            json_text = re.sub(r'\\+\'', '\'', json_text)
            data_dict = json.loads(json_text)
            if 'step' in data_dict:
                cur_step = data_dict['step']
                rematch = re.match('\[(\d\d:\d\d:\d\d)\]', str(line))
                if rematch:
                    # Get date, as the logs only provide the time
                    format = "%Y-%m-%d"
                    self.game_score_dict[cur_step]['Time_Stamp'] = \
                        time.strftime(format, time.localtime()) + " " + rematch.group(1)

                if 'command_result' in data_dict:
                    self.game_score_dict[cur_step].update(data_dict['command_result'])

                if 'goal' in data_dict:
                    self.game_score_dict[cur_step].update(data_dict['goal'])
                    if data_dict['goal']['Distribution'] != 'Uninformed':  # TODO: move this elsewhere?
                        self.score_dict[self.game_index]['groundTruth'] = 1
                    # self.game_score_dict[cur_step]['Goal_Type'] = data_dict['goal']['goalType']
                    # self.game_score_dict[cur_step]['Goal_Achieved'] = data_dict['goal']['goalAchieved']
                    # self.game_score_dict[cur_step]['Novelty_Flag'] = "0"  # TODO: include Novelty Flag from PAL
                if 'gameOver' in data_dict:
                    self.game_score_dict[cur_step]['Game_Over'] = data_dict['gameOver']

        # Case 2: Record a [SCORE] Update from PAL, updating the running totals and the intermediate reward tracking
        if line.find('[SCORE]') != -1 and line.find(line_end_str) != -1:
            score_string = line[line.find('[SCORE]')+7:line.find(line_end_str)]
            scores_dict = {v[0]: v[1] for v in [k.split(':') for k in score_string.split(',')]}
            self.score_dict[self.game_index].update(scores_dict)
            cur_step = int(scores_dict['step'])
            self.game_score_dict[cur_step].update({'running_total_cost': scores_dict['totalCost']})
            self.game_score_dict[cur_step].update({'running_total_score': scores_dict['adjustedReward']})

    def _setup_next_game(self):
        """
        Launch the next game
        Initialize the score_dict variable for the next game.

        # TODO: Flag games that have novelty!
        # noTODO: Flag games where we communicate to agent that novelty exists - are flagged in self._record_score()
        """
        if self.game_index == 0:
            self.tm_thread.queue.put("LAUNCH domain " + self.games[self.game_index])
            self.debug_log.message("LAUNCH domain command issued")

        self.game_score_dict = defaultdict(lambda: defaultdict(lambda: 0))
        self.score_dict = {self.game_index: defaultdict(lambda: 0)}  # Reset Score_Dict as well
        self.score_dict[self.game_index]['game_path'] = self.games[self.game_index]
        # self.score_dict[self.game_index]['startTime'] = PalMessenger.PalMessenger.time_now_str()

        # TODO: Update this based on Tournament Setup & input.
        self.score_dict[self.game_index]['novelty'] = 0
        self.score_dict[self.game_index]['groundTruth'] = 0


    def _gameover_passed_to_agent(self, line):
        """
        Check to see if Agent has been sent the gameOver == True parameter before resetting the game
        :param line: input string (msg in PAL)
        :return: True if gameOver: true passed to client
        """

        line_end_str = '\r\n'
        line_end_str = '\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\n'

        if line.find('{') != -1 and line.find(line_end_str) != -1 and line.rfind('}') != -1:
            json_text = line[line.find('{'):line.rfind('}')+1]
            # json_text = line[line.find('{'):line.find(line_end_str)]  # Make this system agnostic - previously \\r\\n
            # noTODO: Potentially remove this?
            json_text = re.sub(r'\\\\\"', '\'', json_text)
            json_text = re.sub(r'\\+\'', '\'', json_text)
            # Load response into dictionary
            data_dict = json.loads(json_text)
            # Check to see if gameover in msg
            if 'gameOver' in data_dict:
                if data_dict['gameOver']:
                    self.debug_log.message("GameOver = True!")
                    return True

        return False

    def _check_agent_cmd(self, line):
        """
        Checks to see if the Agent has sent PAL any messages yet. If so, PAL will print [AGENT] + the msg
        If so, return true - the agent is running and the gameloop can begin
        :param line: PAL line
        :return: True if agent has sent a msg to PAL and PAL indicates that it successfully received it.
        """
        if line.find('[AGENT]') != -1:
            return True

        return False


class State(Enum):
    INIT_PAL = 0
    LAUNCH_TOURNAMENT = 1
    CLEANUP = 2
    INIT_AGENT = 4
    WAIT_FOR_AGENT_START = 5
    GAME_LOOP = 6
    WAIT_FOR_GAME_READY = 7
    WAIT_FOR_GAMEOVER_TRUE = 8
    TEST = 9
    TRIGGER_RESET = 10
    DETECT_RESET = 11

if __name__ == "__main__":
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "hc:t:g:a:d:x:i:m:l:p:e:",
                                       ["game_count=","tournament=","game_folder=","agent name=", "agent directory=", "agent command=", "max time=", "max tournament time=", "log_dir=", "pal_command=", "sql_err_dir="])
    except getopt.GetoptError:
        print('LaunchTournament.py '
              '-c <game_count> '
              '-t <tournament_name> '
              '-g <game_folder> '
              '-a <agent_name> '
              '-d <agent_directory> '
              '-x <agent_command> '
              '-i <maximum time (sec)> '
              '-l <log_path>'
              '-p <pal_command>'
              '-e <sql_err_dir>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('LaunchTournament.py -h '
                  '-c <game_count> '
                  '-t <tournament_name> '
                  '-g <game_folder> '
                  '-a <agent_name> '
                  '-d <agent_directory> '
                  '-x <agent_command> '
                  '-i <maximum time (sec)> '
                  '-m <max tournament time (minutes)'
                  '-l <log_path>'
                  '-p <pal_command>'
                  '-e <sql_err_dir>')
            sys.exit()
        elif opt in ("-c", "--count"):
            # print(f"Number of Games: {arg}")
            CONFIG.GAME_COUNT = int(arg)
        elif opt in ("-a", "--agent-name"):
            print(f"Agent Name: {arg}")
            CONFIG.AGENT_ID = arg
        elif opt in ("-g", "--game-folder"):
            print(f"Game Folder: {arg}")
            CONFIG.GAMES_FOLDER = arg
        elif opt in ("-t", "--tournament"):
            print(f"Tournament: {arg}")
            CONFIG.TOURNAMENT_ID = arg
        elif opt in ("-d", "--agent-dir"):
            print(f"Agent Directory: {arg}")
            CONFIG.AGENT_DIRECTORY = arg
        elif opt in ("-x", "--agent-exec"):
            print(f"Agent Command: {arg}")
            CONFIG.AGENT_COMMAND_UNIX = arg
            CONFIG.AGENT_COMMAND = arg
        elif opt in ("-p", "--pal-exec"):
            print(f"PAL Command: {arg}")
            CONFIG.PAL_COMMAND_UNIX = arg
            CONFIG.PAL_COMMAND = arg
        elif opt in ("-i", "--max-time"):
            print(f"Max Time (sec): {arg}")
            CONFIG.MAX_TIME = int(arg)
        elif opt in ("-m", "--max-tournament-time"):
            print(f"Max Time (minutes): {arg}")
            CONFIG.MAX_TOURN_TIME = int(arg)
        elif opt in ("-l", "--log-dir"):
            print(f"Log Directory: {arg}")
            CONFIG.LOG_DIR = arg
        elif opt in ("-e", "--sql-err-dir"):
            print(f"SQL Error Log Directory: {arg}")
            CONFIG.SQL_ERR_LOG_DIR = arg
    # test if windows or unix
    if os.name == 'nt':
        pos = 'WIN'
    else:
        pos = 'UNIX'
    pal = LaunchTournament(os=pos)  # TODO: Remove the os command line argument.
    pal.execute()
