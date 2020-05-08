# Quick start guide:
## Windows
* Key dependency: Java JDK 8
	* https://www.oracle.com/java/technologies/javase/javase-jdk8-downloads.html
	* Or as appropriate with Oracle
	* You may have to sign in and create an account.
* Get Git: https://git-scm.com/downloads
	* Download and install with all defaults
* Clone repo (if repo is not already cloned): 
	* Navigate to target folder for installing Polycraft AI Lab
	* Run command prompt/PowerShell
	* git clone https://github.com/StephenGss/PAL.git
* Pull updates (if repo is already cloned):
* Run LaunchPolycraft.bat
	* If it fails, try running ./gradelw runclient from PowerShell in the same window, read the error, and fix it your own based on local configuration
## Ubuntu
* Send the following commands in the terminal:
	* `sudo apt-get update && sudo apt-get upgrade -y`
	* `sudo apt install openjdk-8-jdk openjdk-8-jre`
	* `git`
	* `git clone https://github.com/StephenGss/pal.git`
	* `cd pal/`
	* `chmod +x gradlew`
	* `./gradlew runclient`
* Possible issues
	* The last command, `./gradlew runclient` may fail with the following as part of the error message:
	`Could not determine java version from '#.#.#'.`
		* Solution: Run `sudo update-alternatives --config java`
		* Choose the option with jdk-8
	* The last command, `./gradlew runclient` may fail with the following as part of the error message:
	`Process 'command '/usr/lib/jvm/java-8-openjdk-amd64/bin/java'' finished with non-zero exit value 1`
		* Check the stack trace for mention of `Can't connect to X11 window server using 'localhost:0.0' as the value of the DISPLAY variable.`
		* Agents that will use SENSE_SCREEN must have systems with video cards
		* Other agents may be able to run on these systems, but solutions to this issue are based on your local configuration.

## Interacting with Polycraft AI Lab, platform independent
* Run PAL -> PolycraftAIGym -> testSocket.py
	* Python is available at python.org. It is not required to run or connect to PAL, but it is required to run the demo script.
	* The python console will accept user input.
	* Send "START" to put PAL in a state where it can receive communications
		* Wait for the Polycraft window to change to a plain field
	* Send "RESET domain ../available_levels/pogo_nonov.json
		* Or other level as needed. See Tasks and Novelties
	* Send API sense commands or action commands. Such as:
		* "SENSE_ALL NONAV" to get information about the player's environment
		* "MOVE W" to move forward
		* "BREAK_BLOCK" to break the block immediately in front of the player
		* Many more commands described in Polycraft Bot API section

# Polycraft Bot API
The Polycraft World AI API consists of 28 total different API commands at Release 1.5.0 on 5.4.2020. These commands are broken down into SYSTEM commands, DEV commands, and GAME commands. The GAME commands are further divided into MOVE commands, SENSE commands, INTERACT commands.
## SYSTEM commands: (2 total)
* **START**  
	* no args ever used | called once to start tournaments
* **RESET** domain ../available_tests/pogo_nonov.json
	* the base pogo experiment
* **RESET** domain ../available_tests/hg_nonov.json
	* the base hunter-gatherer experiment
* The following function on the cloud virtual machines for the test harness:
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_1/trial_1/hg_1.1.json
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_1/trial_1000/hg_1.1000.json
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_100/trial_1/hg_100.1.json
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_100/trial_1000/hg_100.1000.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_1/trial_1000/pogo_1.1.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_1/trial_1000/pogo_1.1000.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_100/trial_1000/pogo_100.1.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_100/trial_1000/pogo_100.1000.json
		* -d (domain) path to .json novelty transform 
		* called 1,000 times per tournament to start a new trial
		* different tournaments will run using cloned TA2 agents on different cloud machines
		* novelty will be pre-set in the .jsons and not generated at run-time

## DEV commands: (4 total)
* Dev commands must be enabled by setting a client virtual machine argument: "-Ddev=True" Details on setting this outside of a development environment are still being worked out, as solutions are fickle and system dependent. Please contact us if you need these commands.
* **CHAT** "Hello world."
* **CHAT** /give @p minecraft:stick
	* not used in DRY-RUN Tournaments, but active for debugging/training/development
* The following function on the cloud virtual machine for the test harness.
	* **CREATE_NOVELTY_VARIATIONS** -d ../available_tests/hg_2.X.json -s 42 -i 60
	* **CREATE_NOVELTY_VARIATIONS** -d ../ available_tests/pogo_2.X.json -s -37489 -i 10
		* Novelty generators for level zero (rearranging objects) are not included currently but will be soon
		* not used in DRY-RUN Tournaments, but provides agents in training a simple way to try out different seeds and different intensities during training within the same tournament
		* -d (domain) path to .json novelty transform -s (seed) arbitrary INT -i (intensity) INT 0-100
		* generates novelty at run time for training purposes
* **SPEED** 30
	* not used in DRY-RUN Tournaments, but sets the game speed in ticks per sec (default 20)
* **TELEPORT** 20 4 21 90 0
	* not to be used in DRY-RUN Tournaments, but allows setting player location and view direction.
	* Parameters: [x] [y] [z] [yaw] [pitch]

## GAME commands - MOVE commands: (7 total)
* **SMOOTH_MOVE** w
* **SMOOTH_MOVE** a
* **SMOOTH_MOVE** d
* **SMOOTH_MOVE** x
	* moves 1 meter forward (w), left (a), right (d) or back (x) continuously
* **SMOOTH_MOVE** q
* **SMOOTH_MOVE** e
* **SMOOTH_MOVE** z
* **SMOOTH_MOVE** c
	* moves sqrt (2) distance diagonally with (q,e,z,c)
* **MOVE** w
	* parameters: w,a,d,x, or q,e,z,c as in SMOOTH_MOVE (does not interpolate during move)
* **SMOOTH_TURN** 15
	* alters player's horizontal facing direction (yaw) in 15-degree increments
* **TURN** -15
	* alters player's horizontal facing direction (yaw) in 15-degree increments (no interpolation)
* **SMOOTH_TILT** 90
* **SMOOTH_TILT** FORWARD
* **SMOOTH_TILT** DOWN
* **SMOOTH_TILT** UP
	* alters player's vertical facing direction (pitch) in 15-degree increments
	* three higher level commands set player looking forward (0) or down (-90) or up (90)
* **TILT** -90
	* alters player's vertical facing direction (pitch) in 15-degree increments (no interpolation)
	* also can be parameterized with FORWARD, DOWN and UP
* **TP_TO** 20 4 21 
	* as in TELEPORT without adjusting yaw and pitch
* **TP_TO** 20 4 21 2
	* as in teleport without adjusting yaw and pitch, but with an offset straight backwards
	* offset must yield allowable move_to location or command fails
* **TP_TO** 7101
	* teleports to the location of an entity with entity_ID "7101"

## GAME commands - SENSE commands: (8 total)
* **CHECK_COST**
	* returns the stepCost incurred since the last RESET command
* **REPORT_BLOCK** 0 6 2
	* special call for hg domain for denser rewards | reports whether a floor block is special or not
	* params: [0 = normal block, 1 = macguffin, 2 = target] [x][z]
* **REPORT_NOVELTY**
	* indicates that you have detected novelty with optional parameters | [-l novelty level]
	* [-c confidence interval 0f:100f] [-g game novelty was detected] [-m user-defined message]
* **SENSE_INVENTORY**
	* returns contents of player inventory in .json format
* **SENSE_LOCATIONS**
	* returns senseable world environment (blocks, entities and locations) as .json
* **SENSE_RECIPES**
	* Returns the list of recipes available in the experiment
* **SENSE_SCREEN**
	* Returns pixels sent to the display output window, in the form of a string listing an array of integers
* **SENSE_ALL**
* **SENSE_ALL NONAV**
	* returns inventory, recipe and location information in .json | NONAV parameters omits information which is not needed for agents that do not navigate the world

## GAME commands - INTERACT commands: (9 total)

* **SELECT_ITEM** polycraft:wooden_pogo_stick
	* sets a specific item from your inventory in your hand as the active item (e.g. tool or block)
* **USE_HAND**
	* to open doors with bare hand (ignores item in hand to interact)
* (inactive) USE_ITEM
	* will be added after dry-run. NOT in release 1.5.0
* **BREAK_BLOCK**
	* breaks block directly in front of player with selected item
	* selected item and block type yield stepCost of action
* **CRAFT** 1 minecraft:log 0 0 0
	* note that CRAFT must be followed by a "1"
	* crafts 4 Planks
* **CRAFT** 1 minecraft:planks 0 minecraft:planks 0
	* crafts 4 Sticks 
* **CRAFT** 1 minecraft:planks minecraft:planks 0 minecraft:planks minecraft:stick 0 0 minecraft:stick  0
	* crafts a Wooden Axe 
* **CRAFT** 1 minecraft:planks minecraft:stick minecraft:planks minecraft:planks 0 minecraft:planks 0 minecraft:planks 0
	* crafts a Tree Tap
* **CRAFT** 1 minecraft:stick minecraft:stick minecraft:stick minecraft:planks minecraft:stick minecraft:planks 0 polycraft:sack_polyisoprene_pellets 0
	* crafts a Wooden Pogo Stick
* **EXTRACT_RUBBER**
	* moves polycraft:sack_polyisoprene_pellets from polycraft:tree_tap to player inventory
* PLACE_BLOCK polycraft:macguffin 
	* will be added after dry-run. NOT in release 1.5.0
* **PLACE_TREE_TAP**
	* calls PLACE_BLOCK polycraft:tree_tap (and processes extra rules)
* **PLACE_CRAFTING_TABLE**
	* calls PLACE_BLOCK minecraft:crafting_table  (and processes extra rules)
* **PLACE_MACGUFFIN**
	* calls PLACE_BLOCK polycraft:macguffin (and processes extra rules)
