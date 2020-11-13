#!/usr/bin/env python

import socket, random, time, json, os

print("INITIALIZING")

AGENT_HOST = "127.0.0.1"
AGENT_PORT = 9000


# if 'PAL_AGENT_PORT' in os.environ:
#     sock.connect((AGENT_HOST, int(os.environ['PAL_AGENT_PORT'])))
#     print('Using Port: ' + os.environ['PAL_AGENT_PORT'])
# else:
#     sock.connect((AGENT_HOST, AGENT_PORT))
#     print(f'Using Port: {str(AGENT_PORT)}')

command_stream = [
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move q",
    "smooth_move q",
    "smooth_turn 90",
    "smooth_move w",
    "smooth_move w",
    "smooth_move e",
    "smooth_move e",
    "smooth_move e",
    "smooth_move e",
    "smooth_move e",
    "smooth_move w",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move d",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move w",
    "smooth_move q",
    "smooth_move w",
    "smooth_move w",
    "smooth_tilt down",
    "smooth_move w",
    "place_macguffin"
]
reset = False
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((AGENT_HOST, AGENT_PORT))

    while True:
        loop_commands = command_stream

        if reset:
            ## Wait for server to reset
            loop_commands = ["SENSE_ALL"]

        for command in loop_commands:
            sock.send(str.encode(command + '\n'))
            print(command)
            BUFF_SIZE = 4096  # 4 KiB
            data = b''
            while True:
                part = sock.recv(BUFF_SIZE)
                data += part
                if len(part) < BUFF_SIZE:
                    # either 0 or end of data
                    break
            if data is not None:
                try:
                    data_dict = json.loads(data)
                    print(data_dict)
                    if reset: # Check to see if the reset is complete.
                        if 'command_result' in data_dict:
                            if 'result' in data_dict['command_result']:
                                if data_dict['command_result']['result'] == 'SUCCESS' and not data_dict['gameOver']:
                                    print("Agent detected Game Reset Complete")
                                    reset = False
                    if data_dict['gameOver']:
                        print("Agent Detected Game Over")
                        reset = True
                        break
                except ValueError:
                    pass #just keep going otherwise.

            time.sleep(0.1)

print("Socket closed")
