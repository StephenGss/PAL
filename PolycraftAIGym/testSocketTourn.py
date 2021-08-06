#!/usr/bin/env python

import socket, random, time, json, os
import tempfile
import shutil
import zipfile

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

while run:  # main loop
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
            zipPath = "C:\\Users\\Stephen\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\huga-12M-tournaments-zipped\\HUGA_100game_full_eval_unknown_mode\\" \
                      + userInput.split(" ")[1][0:16] + "\\" + userInput.split(" ")[1][17:22] + "\\" + \
                      userInput.split(" ")[
                          1] + ".zip"
        else:
            zipPath = "C:\\Users\\Stephen\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\pogo-12M-tournaments-zipped\\POGO_100game_12M_full_evaluation_unknown_mode\\" \
                      + userInput.split(" ")[1][0:16] + "\\" + userInput.split(" ")[1][17:22] + "\\" + userInput.split(" ")[
                          1] + ".zip"
        print(zipPath)
        file = zipfile.ZipFile(zipPath)
        file.extractall(path=dirpath)

        filename = None
        for subdir, dirs, files in os.walk(dirpath):
            for f_name in files:
                if f_name.startswith(
                        userInput.split(" ")[1][0:23] + userInput.split(" ")[1][25:33] + "_" + userInput.split(" ")[
                            2]) and f_name.endswith('.json'):
                    filename = subdir + "\\" + f_name
        print(filename)
        userInput = "Launch domain " + filename

    if userInput == 'exit':  # wait for user input commands
        run = False
    elif userInput == 'wonder':  # testing automatic commands
        count = 200
        while count > 0:
            sock.send(random.choice(movement))
            sock.close()  # socket must be closed between after command
            time.sleep(0.5)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            count = count - 1
    else:
        sock.send(str.encode(userInput + '\n'))

    # Look for the response
    amount_received = 0
    amount_expected = 16
    # if userInput.startswith('DATA') or userInput.startswith('LL'):	 # if we need to receive something, we have to listen for it. Maybe this should be a separate thread?
    # 	data = ''
    # 	data = sock.recv(10240).decode()
    # 	data_dict = json.loads(data)
    # 	print (data_dict)
    # if not userInput.startswith('START'):
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
