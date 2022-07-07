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
PAL_COMMAND_UNIX = "singularity run --fakeroot --writable-tmpfs --pwd /PAL  $SCRATCH/pal-test.simg sudo bash -c 'rm -f /root/.gradle/caches/modules-2/modules-2.lock && xvfb-run -a ./gradlew --no-daemon --stacktrace runclient'"
# PAL_COMMAND_UNIX = "singularity run --fakeroot --writable-tmpfs --pwd /PAL --net --network-args \"portmap=9000:9000/tcp\" --network-args \"portmap=9005:9005/tcp\" $SCRATCH/pal-test.simg sudo bash -c 'rm -f /root/.gradle/caches/modules-2/modules-2.lock && xvfb-run -a ./gradlew --no-daemon --stacktrace runclient'"
# PAL_COMMAND_UNIX = "xvfb-run -s '-screen 0 1280x1024x24' ./gradlew --no-daemon --stacktrace runclient"

PAL_DOCKER_CONTAINER = "pal-9000"
PAL_DOCKER_LABEL = "pal"
PAL_DOCKER_TAG = "latest"
PAL_DOCKER_AGENT_PORT = 9000
PAL_DOCKER_TM_PORT = 9005
PAL_COMMAND_DOCKER = "docker run --name pal-test-9000 -d -w /PAL -p 9000:9000 pal:latest sudo xvfb-run -a ./gradlew --no-daemon --stacktrace runclient"
PAL_COMMAND_SING = "singularity run --pwd /PAL pal_latest-2021-04-16-78889fd4123b.simg sudo xvfb-run -a ./gradlew --no-daemon --stacktrace runclient"
# PAL_COMMAND_DOCKER = "docker run --name pal-test-9000 -d -w /PAL -p 9000:9000 pal:latest sudo xvfb-run -a ./gradlew --no-daemon --stacktrace runclient"

MAX_AGT_CMD_WAIT = 30   # max time between agent commands. If we exceed this, the agent is likely frozen

## CONFIGURABLE ##################################### CLI Commands ####################################
MAX_TIME = 300                                      # change using -i <time>
MAX_TOURN_TIME = 2880                               # change using -m <minutes> 48 hours default
TOURNAMENT_ID = "Nonov_Pogo_Test_6_1000g"           # change using -t <tournament_name>
AGENT_DIRECTORY = "../agents/change/me/"            # change using -d <agent/start/script/folder/>
AGENT_COMMAND = "py hg_agent.py"                    # change using -x <windows cmd to launch script - Windows OS only>
AGENT_COMMAND_UNIX = "python hg_agent.py"           # change using -x <bash cmd to launch script - x changes both vars>
AGENT_ID = f"MY_AGENT_ID"                           # change using -a <agent_name>
GAME_COUNT = 25                                     # change using -c <count>
GAMES_FOLDER = "../change/me/please/"               # change using -g <rel_path/to/games/folder>
SPEED = 20                                          # change using -s <ticks_per_second>
LOG_DIR = 'Logs/'                                   # change using -l <log_dir>
SQL_ERR_LOG_DIR = None                              # change using -e <sql_err_dir>
MAX_STEP_COUNT = 10000                              # change using -q <max_step_count>