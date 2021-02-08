#!/usr/bin/env python

import socket, random, time, json, os, datetime

HOST = "127.0.0.1"
PORT = 9000
packet_sizes = []

movement = ['movenorth', 'movesouth', 'moveeast', 'movewest']

run = True

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if 'PAL_PORT' in os.environ:
    sock.connect((HOST, int(os.environ['PAL_PORT'])))
    print('Using Port: ' + os.environ['PAL_PORT'])
else:
    sock.connect((HOST, PORT))
    print('Using Port: ' + str(PORT))

while run:  # main loop
    userInput = input()
    if userInput == 'exit':  # wait for user input commands
        run = False
    elif userInput.startswith('speedtest'):  # testing automatic commands
        command1 = 'MOVE w\n'
        command2 = 'MOVE x\n'
        if userInput.endswith('2'):
            command1 = 'CRAFT 1 minecraft:planks minecraft:planks minecraft:planks minecraft:planks\n'
            command2 = command1
        if userInput.endswith('3'):
            command1 = 'tp_to 2,4,6\n'
            command2 = command1
        totalCount = 100
        count = totalCount
        startTime = datetime.datetime.now()
        while count > 0:
            if count % 20 >= 10:
                sock.send(str.encode(command1))
            else:
                sock.send(str.encode(command2))
            # time.sleep(0.0001)
            if True:
                BUFF_SIZE = 4096  # 4 KiB
                data = b''
                while True:
                    part = sock.recv(BUFF_SIZE)
                    data += part
                    if len(part) < BUFF_SIZE:
                        # either 0 or end of data
                        break
            count = count - 1
        endTime = datetime.datetime.now()
        timeDiff = endTime - startTime
        ms = (timeDiff.microseconds / 1000) + timeDiff.seconds * 1000
        print("Time Taken: " + str(ms) + "ms")
        print("FPS: " + str(totalCount / (ms / 1000)))

        sock.send(str.encode(userInput + '\n'))
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
    packet_sizes = []
    if True:
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = sock.recv(BUFF_SIZE)
            data += part
            packet_sizes.append(len(part))
            print(part[-1])
            if len(part) < BUFF_SIZE or part[-1] == 10:
                # either 0 or end of data
                break
        print(data)
        print('packets: ' + str(packet_sizes))
        print('message size: ' + str(len(data)))
# data_dict = json.loads(data)
# print(data_dict)
sock.close()

print("Socket closed")
