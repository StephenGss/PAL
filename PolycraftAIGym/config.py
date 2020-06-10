######## TOURNAMENT CONFIGS #########
"""
Some of these parameters (in the ## CONFIGURABLE ## Subsection) can be modified by command-line arguments
to LaunchTournament.py

The others will need to be modified here based on local run configurations. See the README or email
dhruv@polycraftworld.com for additional clarification.

"""

# Tournament Ends if Total Step Cost exceeds 1M - not easy for 5 minute games ##
MAX_STEP_COST = 1000000

# For Systems with Graphics Cards, Use this instead
# PAL_COMMAND_UNIX = "./gradlew runclient"
PAL_COMMAND_UNIX = "xvfb-run -s '-screen 0 1280x1024x24' ./gradlew --no-daemon runclient"

# Optional Commands that aren't required if AGENT_COMMAND_UNIX is changed
LOG_FILE_DIR = "polycraft/pal/private_tests/agent_logs_sift_1000g/"
_AGENT_SCRIPT = f"./sift_tournament_agent_launcher.sh {LOG_FILE_DIR}"

## CONFIGURABLE ##################################### CLI Commands ####################################
MAX_TIME = 300                                      # change using -i <time>
TOURNAMENT_ID = "Nonov_Pogo_Test_6_1000g"           # change using -t <tournament_name>
AGENT_DIRECTORY = "../agents/SIFT_SVN/code/test/"   # change using -d <agent/start/script/folder/>
AGENT_COMMAND_UNIX = f"{_AGENT_SCRIPT}"             # change using -x <bash cmd to launch script>
AGENT_ID = f"SIFT_AGENT_POGO_003"                   # change using -a <agent_name>
GAME_COUNT = 25                                     # change using -c <count>
GAMES_FOLDER = "../pogo_json"                       # change using -g <rel_path/to/games/folder>
