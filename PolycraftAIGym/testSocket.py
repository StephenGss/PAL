#!/usr/bin/env python

import socket, random, time, json, os, datetime
import cv2
import base64
import numpy as np

HOST = "localhost"
PORT = 9000
last_result = ''
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
    elif userInput == 'start_sample':
        userInput = 'RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00000_I0881_N0.json'
        sock.send(str.encode(userInput + '\n'))
    elif userInput.lower().startswith('show_screen'):
        png_data_b64 = json.loads(data)['screen']['data']
        data = base64.b64decode(png_data_b64)
        # CV2
        nparr = np.frombuffer(data, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # cv2.IMREAD_COLOR in OpenCV 3.1
        # CV
        # img_ipl = cv2.CreateImageHeader((img_np.shape[1], img_np.shape[0]), cv.IPL_DEPTH_8U, 3)
        # cv2.SetData(img_ipl, img_np.tostring(), img_np.dtype.itemsize * 3 * img_np.shape[1])
        cv2.imshow("image", img_np)
        cv2.waitKey(10000)
        cv2.destroyAllWindows()
        continue
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
                    if len(part) < BUFF_SIZE or part[-1] == 10:
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
    if True:
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = sock.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE or part[-1] == 10:
                # either 0 or end of data
                break
        print(data)
        last_result = data
# data_dict = json.loads(data)
# print(data_dict)
sock.close()

print("Socket closed")
