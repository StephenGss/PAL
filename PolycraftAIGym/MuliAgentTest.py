#!/usr/bin/env python
import socket, os, datetime, time, random
import threading

def dummy_agent(id):
    HOST = "127.0.0.1"
    PORT = 9001
    movement = ['MOVE w', 'MOVE a', 'MOVE d', 'MOVE x']

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if 'PAL_PORT' in os.environ:
        sock.connect((HOST, int(os.environ['PAL_PORT'])))
        print(str(id) + 'Using Port: ' + os.environ['PAL_PORT'])
    else:
        sock.connect((HOST, PORT))
        print(str(id) + 'Using Port: ' + str(PORT))
    totalCount = 50
    count = totalCount
    startTime = datetime.datetime.now()
    rand = random.Random()
    # send_command(sock, "RESET -d ../Novelty/output/shell/test_G00000_I0152_N0.json")
    send_command(sock, "RESET nextgame")
    time.sleep(5)
    send_command(sock, "RESET nextgame")
    time.sleep(5)
    send_command(sock, "RESET nextgame")
    time.sleep(5)
    send_command(sock, "RESET nextgame")
    time.sleep(5)
    while count > 0:
        time.sleep(0.0050)
        send_command(sock, movement[rand.randint(a=0, b=3)])
        count = count - 1
    endTime = datetime.datetime.now()
    timeDiff = endTime - startTime
    ms = (timeDiff.microseconds / 1000) + timeDiff.seconds * 1000
    print(str(id) + "Time Taken: " + str(ms) + "ms")
    print(str(id) + "FPS: " + str(totalCount / (ms / 1000)))
    sock.close()

    print(str(id) + "Socket closed")

def send_command(sock, command):
    BUFF_SIZE = 4096  # 4 KiB
    print(str(command))
    sock.send(str.encode(command + "\n"))
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE or part[-1] == 10:
            # either 0 or end of data
            break
    print(data)
    return data

def main():
    for i in range(0, 2):
        x = threading.Thread(target=dummy_agent, args=(i,))
        x.start()
        time.sleep(1.0)


if __name__ == "__main__":
    main()