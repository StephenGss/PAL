#!/usr/bin/env python
# Fast Instance Loader and Action Replay
# Author: Stephen Goss
# Date: 08-09-2021
#
# Exmaple command - '# tournament_name game rundate agent'
# '# POGO_L00_T01_S01_X0100_E_U0012_V2 G00001 113000 CRA_36M
#

import socket, random, time, json, os, pandas
import tempfile
import shutil
import zipfile
import threading
from PolycraftAIGym.AzureConnectionService import AzureConnectionService
from PolycraftAIGym.PalMessenger import PalMessenger
from PolycraftAIGym.ActionReplayAgent import ActionReplayAgent

HOST = "127.0.0.1"
PORT = 9005

movement = ['movenorth', 'movesouth', 'moveeast', 'movewest']

run = True

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
if 'PAL_PORT' in os.environ:
    sock.connect((HOST, int(os.environ['PAL_PORT'])))
    print('Using Port: ' + os.environ['PAL_PORT'])
else:
    sock.connect((HOST, PORT))
    print('Using Port: ' + str(PORT))

dirpath = tempfile.mkdtemp()
print(dirpath)
print('Exmaple command - \'# tournament_name game rundate agent\'')
print('# POGO_L00_T01_S01_X0100_E_U0012_V2 G00001 010502 CRA_36M')

ar = ActionReplayAgent(host='127.0.0.1', port=9000)
ar.connect()
agent_process = None

while run:  # main loop
    if agent_process is not None:
        while len(ar.actionList)>0:
            if agent_process.poll() is not None:
                break
    rand = random.Random
    userInput = input()
    if userInput.startswith('/'):
        if userInput.startswith('/r'):
            seed = random.randrange(999999)
            print(str(seed))
        else:
            # TODO: check this seed. might lead to crashing 297220 and 501793
            # check for adjacent chests 793405
            seed = 180414
        userInput = f'GENTOUR -c ../test -0 ../Novelty/input/huga_v2/huga_lvl_0.json -o ../Novelty/output/huga_test/ -f test -n 1 -w 0,0,1 -s {str(seed)} -R'
    # userInput = f'GENTOUR -c ../test -0 ../Novelty/input/pogo_v2/pogo_lvl_0.json -o ../Novelty/output/pogo_test/ -f test -n 1 -w 0,0,1 -s {str(seed)} -R'
    elif userInput.startswith('#'):
        if(userInput.startswith('# HUGA')):
            zipPath = "C:\\Users\\Stephen\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\97. FILAR\\huga-24M-tournaments-zipped\\HUGA_100game_full_eval_unknown_mode\\" \
                      + userInput.split(" ")[1][0:16] + "\\" + userInput.split(" ")[1][17:22] + "\\" + \
                      userInput.split(" ")[
                          1] + ".zip"
        else:
            zipPath = "C:\\Users\\Stephen\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\97. FILAR\\pogo-24M-tournaments-zipped\\POGO_100game_full_evaluation_unknown_mode\\" \
                      + userInput.split(" ")[1][0:16] + "\\" + userInput.split(" ")[1][17:22] + "\\" + userInput.split(" ")[
                          1] + ".zip"
        print(zipPath)
        file = zipfile.ZipFile(zipPath)
        file.extractall(path=dirpath)

        filename = None
        for subdir, dirs, files in os.walk(dirpath):
            for f_name in files:
                # 12M format
                if f_name.startswith(
                        userInput.split(" ")[1][0:23] + userInput.split(" ")[1][25:33] + "_" + userInput.split(" ")[
                            2]) and f_name.endswith('.json'):
                    filename = subdir + "\\" + f_name
                # check for 24M format
                if f_name.startswith(userInput.split(" ")[1][0:35] + "_" + userInput.split(" ")[2]) \
                        and f_name.endswith('.json'):
                    filename = subdir + "\\" + f_name
        print(filename)

        # get Agent action list
        query = f"""SELECT      STEP_NUMBER,
                                COMMAND,
                                COMMAND_ARGUMENT
                            from {userInput.split(" ")[4]}
                            WHERE TOURNAMENT_NAME = '{userInput.split(" ")[1] + '_' + userInput.split(" ")[3]}' 
                            and GAME_ID = {int(userInput.split(" ")[2][1:6])}
                    ORDER BY STEP_NUMBER
                    """
        pm = PalMessenger(True, False)
        azure = AzureConnectionService(pm)
        actionList = []
        if azure.is_connected():
            data = pandas.read_sql(query, azure.sql_connection)

        # get actionlist from data
        actionList = data['COMMAND'].tolist()

        userInput = "Launch domain " + filename
        sock.send(str.encode(userInput + '\n'))

        # start agent with action list
        ar = ActionReplayAgent(host='127.0.0.1', port=9000)
        ar.connect()
        ar.actionList = data['COMMAND'].tolist()
        ar.argList = data['COMMAND_ARGUMENT'].tolist()
        agent_process = threading.Thread(target=ar.act())
        agent_process.start()

    # Look for the response
    if True:
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = sock.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                # either 0 or end of data
                break
        print(data)
# data_dict = json.loads(data)
# print(data_dict)
sock.close()

shutil.rmtree(dirpath)

print("Socket closed")
