######## TOURNAMENT CONFIGS #########
"""
Most of these parameters (in the ## CONFIGURABLE ## Subsection) can be modified by command-line arguments
to LaunchTournament.py

e.g.
    >> cd /path/to/polycraft/pal/PolycraftAIGym
    >> python LaunchTournament.py -t "Tournament1" -a "My_Agent" -d "../agents/my_agent_folder/"
    ... -x "./launch_my_agent.sh" -g "../path/to/tournament/jsons/" -c 10 -i 600

Will launch a tournament named "Tournament1" using "My_Agent" found in "../agents/my_agent_folder/" executed with
"launch_my_agent.sh" playing the first 10 games (sorted by the name of the JSON - see readme) found in
folder "../path/to/tournament/jsons/" with 600 seconds of time per game.

The others will need to be modified here based on local run configurations. See the README or email
dhruv@polycraftworld.com for additional clarification.

"""
# Tournament Ends if Total Step Cost exceeds 1M - not easy for 5 minute games ##
MAX_STEP_COST = 1000000

# For Windows - (YMMV):
PAL_COMMAND = "gradlew  --stacktrace runclient"
# For Systems with Graphics Cards, Use this instead
# PAL_COMMAND_UNIX = "./gradlew runclient"
# requires xvfb to be installed - see installation instructions
PAL_COMMAND_UNIX = "xvfb-run -s '-screen 0 1280x1024x24' ./gradlew --no-daemon --stacktrace runclient"

# -c 1000 -t "POGO_L00_T01_S01_X0100_A_U9999_V0200FPS_011022" -g "../pogo_100_PN" -a "BASELINE_POGOPLAN_SPEEDTEST" -d "agents/pogo_stick_planner_agent/" -x "python 1_python_miner_PLANNER_FF_1_vDN_EDITS.py"
## CONFIGURABLE ##################################### CLI Commands ####################################
MAX_TIME = 300                                      # change using -i <time>
MAX_TOURN_TIME = 2880                               # change using -m <minutes> 48 hours default
TOURNAMENT_ID = "POGO_L00_T01_S01_X0100_A_U9999"    # change using -t <tournament_name>
AGENT_DIRECTORY = "."                               # change using -d <agent/start/script/folder/>
AGENT_COMMAND = "python pogo_agent.py"              # change using -x <windows cmd to launch script - Windows OS only>
AGENT_COMMAND_UNIX = "python pogo_agent.py"         # change using -x <bash cmd to launch script - x changes both vars>
AGENT_ID = f"MY_AGENT_ID"                           # change using -a <agent_name>
AGENT_COUNT = 5                                     # number of agents, no cli parameter yet
GAMES_PER_AGENT = 10                                # How many games each agent will play
GAME_COUNT = 100                                    # change using -c <count>
GAMES_FOLDER = "../available_tests/shell"           # change using -g <rel_path/to/games/folder>
SPEED = 20                                          # change using -s <ticks_per_second>
