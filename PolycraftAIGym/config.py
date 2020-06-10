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
PAL_COMMAND = "gradlew runclient"
# For Systems with Graphics Cards, Use this instead
# PAL_COMMAND_UNIX = "./gradlew runclient"
# requires xvfb to be installed - see installation instructions
PAL_COMMAND_UNIX = "xvfb-run -s '-screen 0 1280x1024x24' ./gradlew --no-daemon runclient"

## CONFIGURABLE ##################################### CLI Commands ####################################
MAX_TIME = 300                                      # change using -i <time>
TOURNAMENT_ID = "Nonov_Pogo_Test_6_1000g"           # change using -t <tournament_name>
AGENT_DIRECTORY = "../agents/SIFT_SVN/code/test/"   # change using -d <agent/start/script/folder/>
AGENT_COMMAND = "py hg_agent.py"                    # change using -x <windows cmd to launch script - Windows OS only>
AGENT_COMMAND_UNIX = "python hg_agent.py"           # change using -x <bash cmd to launch script - x changes both vars>
AGENT_ID = f"SIFT_AGENT_POGO_003"                   # change using -a <agent_name>
GAME_COUNT = 25                                     # change using -c <count>
GAMES_FOLDER = "../pogo_json/"                      # change using -g <rel_path/to/games/folder>
