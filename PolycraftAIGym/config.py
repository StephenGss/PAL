MAX_STEP_COST = 1000000
MAX_TIME = 300
TOURNAMENT_ID = "Nonov_Pogo_Test_6_1000g"

LOG_FILE_DIR = "polycraft/pal/private_tests/agent_logs_sift_1000g/"
_AGENT_SCRIPT = f"sift_tournament_agent_launcher.sh {LOG_FILE_DIR}"

AGENT_DIRECTORY = "../agents/SIFT_SVN/code/test/"

AGENT_COMMAND_UNIX = f"./{_AGENT_SCRIPT}"

AGENT_ID = f"SIFT_AGENT_POGO_003"

PAL_COMMAND_UNIX = "./gradlew runclient"

# PAL_COMMAND_UNIX = "xvfb-run -s '-screen 0 1280x1024x24' ./gradlew runclient"

#Games now exist outside of this environment.
GAME_COUNT = 50
GAMES_FOLDER = "../pogo_json"
