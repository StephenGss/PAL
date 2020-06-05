import subprocess, threading, socket
import sys, os, signal
import TournamentManager, PalMessenger, AzureConnectionService
from ProcessIOReader import ProcessIOReader
import testThread
from pathlib import Path
import queue
import time
from enum import Enum
import json
import config as CONFIG
from subprocess import PIPE
import re
from collections import defaultdict
from copy import copy, deepcopy
import getopt
import psutil


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
    def __init__(self, os='Win', log_dir='Logs/', args=(), kwargs=None):
        self.commands_sent = 0
        self.total_step_cost = 0
        self.start_time = time.time()
        self.wait_for_gameover_timer = None
        self.wait_for_nextgame_init_timer = None
        self.next_game_initialized_flag = False
        #self.games = CONFIG.GAMES
        #self.games = self._build_game_list(CONFIG.GAME_COUNT)
        self.log_dir = log_dir + f"{PalMessenger.PalMessenger.time_now_str()}/"
        self.SYS_FLAG = os  # Change behavior based on SYS FLAG when executing gradlew
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
        self.tm_lock = threading.Lock()
        self.game_index = 0

        # stdout, stderr = pal_client_process.communicate()
        agent_thread = None
        self.pal_client_process = None
        self.current_state = State.INIT_PAL
        self.tournament_in_progress = True
        self.agent_started = False

        ## Results
        self.score_dict = {}
        self.game_score_dict = defaultdict(lambda: defaultdict(lambda: 0))

        ##Logging
        self._create_logs()

        #Load Games
        self.games = self._build_game_list(CONFIG.GAME_COUNT)

    def _build_game_list(self, ct):
        file_type = '.json'
        file_list = []
        rootdir = CONFIG.GAMES_FOLDER
        for subdir, dirs, files in os.walk(rootdir):
            for file in files:
                filepath = subdir + os.sep + file
                if filepath.endswith(file_type):
                    file_list.append(filepath)

        self.debug_log.message(f"Game List created. {len(file_list)} games read. {len(file_list[:ct])} games will be played")
        sorted_files = self._sort_files(file_list)[:ct]

        self.debug_log.message(f"sorted games to be played: {sorted_files}")
        return sorted_files

    def _sort_files(self, files):
        sorted_dict = {}
        for file in files:
            values = re.search("_G(\d+)_", file)
            if not values:
                raise ValueError("Error - files are not named correctly! "+ file)
            sorted_dict[int(values.groups()[0])] = file

        sorted_file_list = []
        for i in sorted(sorted_dict.keys()):
            sorted_file_list.append(sorted_dict[i])

        return sorted_file_list

    def _create_logs(self):
        """
        Creates the log file handlers
        Re-run after each game to separate the log files appropriately.
        :return:
        """
        # self.log_port_activity = True
        log_dir = self.log_dir
        log_port_file = Path(log_dir) / f"PAL_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str()}"
        agent_port_file = Path(log_dir) / f"Agent_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str()}"
        log_debug_file = Path(log_dir) / f"Debug_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str()}"
        log_speed_file = Path(log_dir) / f"speed_log_game_{self.game_index}_{PalMessenger.PalMessenger.time_now_str()}"
        # log_port_file = Path(log_dir) / "port_log.txt"  # This file won't be used; see issue_reset()
        sent_print_bool = False  # PAL commands are short enough to put in the console
        sent_log_write_bool = True  # Log everything sent to the port to a text file
        recd_print_bool = False  # PAL responses are often long and ungainly; no need to print them
        recd_log_write_bool = True  # Log everything that comes from the port to a text file
        debug_print_bool = True  # For useful stuff, send it to the console
        debug_log_write_bool = True  # For now, log all debug data to another text file.
        speed_print_bool = True         # For useful stuff, send it to the console
        speed_log_write_bool = True     # For now, log all debug data to another text file.

        # # I recognize that some utility like logging may be better, but whatever:
        self.agent_log = PalMessenger.PalMessenger(sent_print_bool, sent_log_write_bool, agent_port_file,
                                                   log_note="AGENT: ")
        self.PAL_log = PalMessenger.PalMessenger(recd_print_bool, recd_log_write_bool, log_port_file, log_note="PAL: ")
        # self.junk_log = PalMessenger(junk_print_bool, junk_log_write_bool, log_note="JUNK: ")
        self.debug_log = PalMessenger.PalMessenger(debug_print_bool, debug_log_write_bool, log_debug_file,
                                                   log_note="DEBUG: ")
        self.speed_log = PalMessenger.PalMessenger(speed_print_bool, speed_log_write_bool, log_speed_file,
                                                   log_note="FPS: ")

    def _check_ended(self, line):
        """
        Check the stdout to see if game ending conditions are met
        :param line: Current Line in the STDOUT of either PAL or AGENT threads
        :return: True if the game has ended.
        """
        # NoTODO: Track stepcost to call reset -- completed
        # TODO: Track total reward to call reset. Not for dry-run
        # NoTODO: Track total run time to call reset -- completed
        # TODO: Track agent giveup to call reset -- completed?
        # NoTODO: Track end condition flag to call reset -- completed

        line_end_str = '\\r\\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\\n'
        ## Agent Giveup check:
        if line.find('[AGENT]GIVE_UP') != -1:
            msg = 'Agent Gives Up'
            self.debug_log.message(f"Game Over: {msg}")
            self.score_dict[self.game_index]['success'] = 'False'
            self.score_dict[self.game_index]['success_detail'] = msg
            return True

        if line.find('{') != -1 and line.find(line_end_str) != -1:
            json_text = line[line.find('{'):line.find(line_end_str)]  # Make this system agnostic - previously \\r\\n
            # TODO: Potentially remove this?
            json_text = re.sub(r'\\\\\"', '\'', json_text)
            json_text = re.sub(r'\\+\'', '\'', json_text)
            data_dict = json.loads(json_text)
            self.commands_sent += 1
            self.total_step_cost += data_dict["command_result"]["stepCost"]
            #self.score_dict[self.game_index].update({'elapsed_time': time.time() - self.start_time})

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
            #if self.score_dict[self.game_index]['elapsed_time'] > CONFIG.MAX_TIME:
             #   msg = 'time exceeded limit'
              #  self.debug_log.message(f"Game Over: {msg}")
               # self.score_dict[self.game_index]['success'] = 'False'
                #self.score_dict[self.game_index]['success_detail'] = msg
                #return True
            # if self.commands_sent > 10000:
            #     return True

        ## Check If Game Timed out.
        self.score_dict[self.game_index].update({'elapsed_time': time.time() - self.start_time})
        if self.score_dict[self.game_index]['elapsed_time'] > CONFIG.MAX_TIME:
            msg = 'time exceeded limit'
            self.debug_log.message(f"Game Over: {msg}")
            self.score_dict[self.game_index]['success'] = 'False'
            self.score_dict[self.game_index]['success_detail'] = msg
            return True
        
        return None

    @DeprecationWarning
    def read_output(self, pipe, q, timeout=1):
        """reads output from `pipe`, when line has been read, puts
    line on Queue `q`"""
        # read both stdout and stderr

        flag_continue = True
        while flag_continue and not pipe.stdout.closed and not pipe.stderr.closed:
            l = pipe.stdout.readline()
            q.put(l)
            l2 = pipe.stderr.readline()
            q.put(l2)

    def _check_queues(self):
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
        except queue.Empty:
            pass

        # write output from procedure B (if there is any)
        try:
            l = self.q2.get(False, timeout=0.025)
            self.agent_log.message(str(l))
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
        # Launch Minecraft Client
        self.debug_log.message("PAL command: " + self.pal_process_cmd)
        self.pal_client_process = subprocess.Popen(self.pal_process_cmd, shell=True, cwd='../', stdout=subprocess.PIPE,
                                                   stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.PAL_reader = ProcessIOReader(self.pal_client_process,  out_queue=self.q, name="pal")

        # self.pa_t = threading.Thread(target=self.read_output, args=(self.pal_client_process, self.q))
        # self.pa_t.daemon = True
        # self.pa_t.start()  # Kickoff the PAL Minecraft Client
        self.debug_log.message("PAL Client Initiated")

        while self.tournament_in_progress:

            # grab the console output of PAL
            next_line = self._check_queues()

            # first check if we crashed or something... hopefully  this doesn't happen
            self.pal_client_process.poll()

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

            # Begin the Game Loop
            elif self.current_state == State.GAME_LOOP:

                # Update the score_dict
                self._record_score(str(next_line))
                self._check_novelty(str(next_line))

                # check if the game has ended somehow (stepcost, max reward, max runtime, agent gave up, game ended)
                if self._check_ended(str(next_line)):

                    next_game_idx = self.game_index + 1
                    # Check if the tournament is over
                    if next_game_idx >= len(self.games):
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
                #TODO: adjust this hang time if necessary?
                MAX_HANG_TIME = 4  # seconds - based on avg ~ 0.25 actions/second + 1 second buffer
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
                # self.wait_for_nextgame_init_timer = time.time()

            # Wait for reset to complete; then reset the game loop
            elif self.current_state == State.DETECT_RESET:

                # Typical Scenario: below text shows up after the reset is triggered.
                # However, case exists where messages may come faster than we can process
                # New solution: Look for this line and set a global flag in the _check_queues() function

                # FIXME: Should I enable this behaviour?
                # if "[EXP] game initialization completed" in str(next_line) or self.next_game_initialized_flag:
                if "[EXP] game initialization completed" in str(next_line):
                    self.debug_log.message("Reset Complete. Switching to Game Loop... ")
                    self.current_state = State.GAME_LOOP
                    self.start_time = time.time() # Start Time at this point.
                    self.score_dict[self.game_index]['startTime'] = PalMessenger.PalMessenger.time_now_str()
                    self.next_game_initialized_flag = False


        #output = self.pal_client_process.communicate()[0]
        exitCode = self.pal_client_process.returncode

        # TODO: Safe to remove? Not sure how this is helpful.
        if exitCode == 0 or exitCode is None:
            return
        else:
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
        self.debug_log.message("Initializing Agent Thread: python hg_agent.py")

        self.agent = subprocess.Popen(self.agent_process_cmd, shell=True, cwd=CONFIG.AGENT_DIRECTORY, stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.agent_reader = ProcessIOReader(self.agent, out_queue=self.q2, name='agent')
        # self.pb_t = threading.Thread(target=self.read_output, args=(self.agent, self.q2))
        self.agent_started = True
        # self.pb_t.daemon = True
        # self.pb_t.start()
        self.debug_log.message("Launched AI Agent")

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
        # if azure.is_connected():
        #     azure.send_score_to_azure(score_dict=self.score_dict, game_id=self.game_index)
        #     azure.send_game_details_to_azure(game_dict=self.game_score_dict, game_id=self.game_index)
        #     azure.upload_pal_messenger_logs(palMessenger=self.agent_log, log_type="agent", game_id=self.game_index)
        #     azure.upload_pal_messenger_logs(palMessenger=self.PAL_log, log_type="pal", game_id=self.game_index)
        #     azure.upload_pal_messenger_logs(palMessenger=self.debug_log, log_type="debug", game_id=self.game_index)
        #     azure.upload_pal_messenger_logs(palMessenger=self.speed_log, log_type='speed', game_id=self.game_index)
        self.game_index += 1
        self._create_logs()

    def _update_azure(self, game_index, score_dict, game_dict, debug_log, agent_log, PAL_log, speed_log):
        # self.pb_t = threading.Thread(target=self.read_output, args=(self.agent, self.q2))
        azure = AzureConnectionService.AzureConnectionService(debug_log)
        # threads = None
        if azure.is_connected():
            # parallel process all uploads!
            # threads.append(threading.Thread(name="send_scores", target=azure.send_score_to_azure, args=(self.score_dict, self.game_index)))
            # threads.append(threading.Thread(name="send_game_score", target=azure.send_game_details_to_azure, args=(self.game_score_dict, self.game_index)))
            azure.send_summary_to_azure(score_dict=score_dict, game_id=game_index)
            azure.send_game_details_to_azure(game_dict=game_dict, game_id=game_index)
            # threads.append(threading.Thread(name="upld_agent", target=azure.upload_pal_messenger_logs, args=(self.agent_log, self.game_index, "agent")))
            # threads.append(threading.Thread(name="upld_pal", target=azure.upload_pal_messenger_logs, args=(self.PAL_log, self.game_index, "pal")))
            # threads.append(threading.Thread(name="upld_debug", target=azure.upload_pal_messenger_logs, args=(self.debug_log, self.game_index, "debug")))
            # speedlog = threading.Thread(target=azure.upload_pal_messenger_logs, args=(self.agent_log, self.game_index, "agent"))
            azure.upload_pal_messenger_logs(palMessenger=agent_log, log_type="agent", game_id=game_index)
            azure.upload_pal_messenger_logs(palMessenger=PAL_log, log_type="pal", game_id=game_index)
            azure.upload_pal_messenger_logs(palMessenger=debug_log, log_type="debug", game_id=game_index)
            azure.upload_pal_messenger_logs(palMessenger=speed_log, log_type='speed', game_id=game_index)
        #     for i in threads:
        #         i.start()
        # return threads

    def _tournament_completed(self):
        """
        Tournament Complete - initiate cleanup of threads
        TODO: Send the score_dict() to a SQL Server or save log files on the Azure Cloud
        :return:
        """
        self.debug_log.message("Tournament Completed: " + str(len(self.games)) + "games run")
        sys.stdout.flush()
        # os.kill(self.agent.pid, signal.SIGTERM)
        # os.kill(self.pal_client_process.pid, signal.SIGTERM)
        self.tm_thread.kill()
        if self.threads is not None:
            self.threads.join()

        self._kill_process_children(5)

        self.tm_thread.join(5)
        self.tournament_in_progress = False

    def _kill_process_children(self, timeout):
        # Kill the client process first to stop it from sending messages to the server
        procs = list(psutil.Process(os.getpid()).children(recursive=True))
        for p in procs:
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        gone, alive = psutil.wait_procs(procs, timeout=timeout)
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass

    def _reset_and_flush(self):
        self.tm_thread.queue.put("RESET domain " + self.games[self.game_index + 1])
        self.debug_log.message("RESET domain command sent to tm_thread.")
        # We think clearing the queue are causing us to miss key log outputs
        # with self.q.mutex:
        #     self.q.queue.clear()
        # with self.q2.mutex:
        #     self.q2.queue.clear()

    def _trigger_reset(self):
        """
        Trigger a reset in PAL - setting the stage for the next game
        :return:
        """
        self.commands_sent = 0
        self.total_step_cost = 9
        self._setup_next_game()
        # if self.threads is not None: #TODO: is this necessary?
        #     self.threads.join()
                # i.join()
        #Flush queues for now - noTODO: this is necessary to catch the Game Initialization Complete string
        # with self.q.mutex:
        #     self.q.queue.clear()
        # with self.q2.mutex:
        #     self.q2.queue.clear()


        # self.q.clear()
        # self.q2.clear()

    def _check_novelty(self, line):
        """
        Checks to see if the agent reported that Novelty was Detected
        :param line: Current Line in STDOUT
        """
        line_end_str = '\\r\\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\\n'
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
        line_end_str = '\\r\\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\\n'
        if line.find('[CLIENT]{') != -1 and line.find(line_end_str) != -1:
            # Get timestamp:
            json_text = line[line.find('{'):line.find(line_end_str)]  # Make this system agnostic - previously \\r\\n
            # TODO: Potentially remove this?
            json_text = re.sub(r'\\\\\"', '\'', json_text)
            json_text = re.sub(r'\\+\'', '\'', json_text)
            data_dict = json.loads(json_text)
            if 'step' in data_dict:
                cur_step = data_dict['step']
                rematch = re.match(r'b\'\[(\d\d:\d\d:\d\d)\]', str(line))
                # rematch = re.match(r'\[\d\d.\d\d.\d\d\]', line)
                # rematch = re.match(r'(\d\d\d\d.\d\d.\d\d.\d\d.\d\d.\d\d):', line)
                if rematch:
                    # Get date, as the logs only provide the time
                    format = "%Y-%m-%d"
                    self.game_score_dict[cur_step]['Time_Stamp'] = \
                        time.strftime(format, time.localtime()) + " " + rematch.group(1)

                if 'command_result' in data_dict:
                    self.game_score_dict[cur_step].update(data_dict['command_result'])
                    # self.game_score_dict[cur_step]['Command'] = data_dict['command_result']['command']
                    # self.game_score_dict[cur_step]['Command_Arguments'] = data_dict['command_result']['argument']
                    # self.game_score_dict[cur_step]['Command_Result'] = data_dict['command_result']['result']
                    # self.game_score_dict[cur_step]['Command_Message'] = data_dict['command_result']['message']
                    # self.game_score_dict[cur_step]['Step_Cost'] = data_dict['command_result']['stepCost']
                if 'goal' in data_dict:
                    self.game_score_dict[cur_step].update(data_dict['goal'])
                    if data_dict['goal']['Distribution'] != 'Uninformed':  # TODO: move this elsewhere?
                        self.score_dict[self.game_index]['groundTruth'] = 1
                    # self.game_score_dict[cur_step]['Goal_Type'] = data_dict['goal']['goalType']
                    # self.game_score_dict[cur_step]['Goal_Achieved'] = data_dict['goal']['goalAchieved']
                    # self.game_score_dict[cur_step]['Novelty_Flag'] = "0"  # TODO: include Novelty Flag from PAL
                if 'gameOver' in data_dict:
                    self.game_score_dict[cur_step]['Game_Over'] = data_dict['gameOver']

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
        TODO: Flag games where we communicate to agent that novelty exists!
        :return:
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

        #initialize vars - noTODO: make a defaultDict? Not sure if possible -- COMPLETED
        # self.score_dict[self.game_index]['noveltyDetectStep'] = 0
        # self.score_dict[self.game_index]['noveltyDetectTime'] = 0
        # self.score_dict[self.game_index]['noveltyDetect'] = 0

    def _gameover_passed_to_agent(self, line):
        """
        Check to see if Agent has received the gameOver == True parameter before resetting the game
        :param line: input string (msg in PAL)
        :return: True if gameOver: true passed to client
        """

        line_end_str = '\\r\\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\\n'

        if line.find('{') != -1 and line.find(line_end_str) != -1:
            json_text = line[line.find('{'):line.find(line_end_str)]  # Make this system agnostic - previously \\r\\n
            # TODO: Potentially remove this?
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
        line_end_str = '\\r\\n'
        if self.SYS_FLAG.upper() != 'WIN':  # Remove Carriage returns if on a UNIX platform. Causes JSON Decode errors
            line_end_str = '\\n'
        if line.find('[AGENT]') != -1 and line.find(line_end_str) != -1:
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

    # seed = 0
    # intensity = 50
    # template_path = '../available_tests/hg_nonov.json'
    # output = '../output'
    # output_name = 'hg_lvl-0'
    try:
        opts, args = getopt.getopt(argv, "hc:t:g:a:d:x:i:",
                                       ["game_count=","tournament=","game_folder=","agent name=", "agent directory=", "agent command=", "max time="])
    except getopt.GetoptError:
        print('LaunchTournament.py -c <game_count> -t <tournament_name> -g <game_folder> -a <agent_name> -d <agent_directory> -x <agent_command>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('LaunchTournament.py -c <game_count> -t <tournament_name> -g <game_folder> -a <agent_name> -d <agent_directory> -x <agent_command>')
            sys.exit()
        elif opt in ("-c", "--count"):
            print(f"Number of Games: {arg}")
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
        elif opt in ("-i", "--max-time"):
            print(f"Max Time (sec): {arg}")
            CONFIG.MAX_TIME = int(arg)



    pal = LaunchTournament(os='UNIX')
    pal.execute()
