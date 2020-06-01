MAX_STEP_COST = 1000000
MAX_TIME = 15
# TOURNAMENT_ID = "Nonov_Pogo_Test_5_1000g"
TOURNAMENT_ID = "Nonov_HG_Test_3_5g"
_AGENT_SCRIPT = "hg_agent.py"
#_AGENT_SCRIPT = "DEBUG=1 Polycraft_Port=9000 ./start-openmind"
#_AGENT_SCRIPT = "./prt polycraft-easy-pogo1.prt"
# _AGENT_CODE = 'code/test/openmind-in-polycraft-tournament.prt'
#_AGENT_SCRIPT = f"code/prt/prt -vD {_AGENT_CODE}"
# LOG_FILE_DIR = "/home/azureuser-1/polycraft/pal/private_tests/agent_logs_sift_1000g/"
# _AGENT_SCRIPT = f"sift_tournament_agent_launcher.sh {LOG_FILE_DIR}"
# _AGENT_SCRIPT = "docker run --rm -e PAL_AGENT_PORT=9000 --network:=host openmind:azureuser"
#_AGENT_SCRIPT = "docker run --rm -e PAL_AGENT_PORT=9000 --network=host sri/polycraftai:nopal 'python -m polycraftai.tournament_test --polycraft_verbose_protocol'"
#_AGENT_SCRIPT = "./play.sh"
# _AGENT_SCRIPT = "../private_tests/DO_Sarsa_Agent/DO_Pogo_Coordinator.py"
# _AGENT_SCRIPT = "1_python_miner_RL_7_trained_2_DN_EDITS.py"
# AGENT_DIRECTORY = "../private_tests/Naive_pogo_agent/trained_pogo_agent2/"
AGENT_DIRECTORY = "./"
#AGENT_DIRECTORY = "../private_tests/SIFT_SVN/"
#AGENT_DIRECTORY = "../private_tests/SIFT_SVN/code/tools/"
# AGENT_DIRECTORY = "../private_tests/SIFT_SVN/code/test/"
#AGENT_DIRECTORY = "../private_tests/TUFTS/"
# AGENT_DIRECTORY = "../private_tests/sri_dryrun_mock/"
#AGENT_COMMAND_UNIX = f"./{_AGENT_SCRIPT}"
# AGENT_COMMAND_UNIX = f"./{_AGENT_SCRIPT}"
#AGENT_COMMAND_UNIX = f"{_AGENT_SCRIPT}"
#AGENT_COMMAND_UNIX = f"/bin/sh build.sh && {_AGENT_SCRIPT}"
# AGENT_COMMAND_UNIX = f"{_AGENT_SCRIPT}"
# AGENT_ID = f"SIFT_AGENT_POGO_003"
AGENT_ID = f"{_AGENT_SCRIPT.split('.')[0]}_BASIC"
# AGENT_COMMAND = f"py {_AGENT_SCRIPT}"
AGENT_COMMAND_UNIX = f"python {_AGENT_SCRIPT}"
# AGENT_COMMAND_UNIX = f"sudo ./{_AGENT_SCRIPT}"
PAL_COMMAND = "gradlew runclient"
#PAL_COMMAND_MAC = "/bin/sh gradlew runclient"
PAL_COMMAND_UNIX = "./gradlew runclient"
# PAL_COMMAND_UNIX = "xvfb-run -s '-screen 0 1280x1024x24' ./gradlew runclient"

#Games now exist outside of this environment.
GAME_COUNT = 5
# GAMES_FOLDER = "../pogo_json"
GAMES_FOLDER = "../HG_LVL0"

GAMES = [
         # "../available_tests/hg_nonov.json",
         # "../available_tests/hg_nonov.json",
         #"../available_tests/hg_nonov.json",
         #"../available_tests/hg_nonov.json",
         #"../available_tests/hg_nonov.json",
         #"../available_tests/hg_nonov.json",
         # "../available_tests/hg_nonov.json",
         # "../available_tests/hg_nonov.json",
          "../available_tests/pogo_nonov.json",
          "../available_tests/pogo_nonov.json",
          "../available_tests/pogo_nov_lvl-0_type-2.json",
          "../available_tests/pogo_nov_lvl-0_type-2.json",
          "../available_tests/pogo_nov_lvl-1_type-1.json",
          "../available_tests/pogo_nov_lvl-1_type-1.json",
          "../available_tests/pogo_nonov.json",
          "../available_tests/pogo_nonov.json",
          "../available_tests/pogo_nonov.json",
         ]
