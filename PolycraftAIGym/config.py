MAX_STEP_COST = 30000
MAX_TIME = 20
TOURNAMENT_ID = "DN_DEMO_TOURNEY_3"
_AGENT_SCRIPT = "hg_agent.py"
# _AGENT_SCRIPT = "play.sh"
# _AGENT_SCRIPT = "../private_tests/DO_Sarsa_Agent/DO_Pogo_Coordinator.py"
# _AGENT_SCRIPT = "1_python_miner_RL_7_trained_2_DN_EDITS.py"
# AGENT_DIRECTORY = "../private_tests/Naive_pogo_agent/trained_pogo_agent2/"
AGENT_DIRECTORY = "./"
# AGENT_DIRECTORY = "../private_tests/TUFTS/"
AGENT_ID = f"{_AGENT_SCRIPT.split('.')[0]}_005"
AGENT_COMMAND = f"py {_AGENT_SCRIPT}"
AGENT_COMMAND_UNIX = f"python {_AGENT_SCRIPT}"
# AGENT_COMMAND_UNIX = f"sudo ./{_AGENT_SCRIPT}"
PAL_COMMAND = "gradlew runclient"
# PAL_COMMAND_UNIX = "/bin/sh gradlew runclient"
PAL_COMMAND_UNIX = "xvfb-run -s \"-screen 0 1280x1024x24\" ./gradlew runclient"
GAMES = [
         # "../available_tests/hg_nonov.json",
         # "../available_tests/hg_nonov.json",
         "../available_tests/hg_nonov.json",
         "../available_tests/hg_nonov.json",
         "../available_tests/hg_nonov.json",
         "../available_tests/hg_nonov.json",
         # "../available_tests/hg_nonov.json",
         # "../available_tests/hg_nonov.json",
         # "../available_tests/pogo_nonov.json",
         # "../available_tests/pogo_nonov.json",
         # "../available_tests/pogo_nov_lvl-0_type-2.json",
         # "../available_tests/pogo_nov_lvl-0_type-2.json",
         # "../available_tests/pogo_nov_lvl-1_type-1.json",
         # "../available_tests/pogo_nov_lvl-1_type-1.json",
         # "../available_tests/pogo_nonov.json",
         # "../available_tests/pogo_nonov.json",
         # "../available_tests/pogo_nonov.json",
         ]