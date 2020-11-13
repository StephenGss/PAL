import subprocess, threading, socket
import sys
from PolycraftAIGym import TournamentManager
import queue

HOST = "127.0.0.1"
TM_PORT = 9000

def execute(command):
    pal_client_process = subprocess.Popen(command, shell=True, cwd='../', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    game_started = False
    path_to_exp = "../available_tests/hg_nonov.json"
    tm_thread = None
    tm_lock = threading.Lock()

    # Poll process for new output until finished
    while True:
        nextline = pal_client_process.stdout.readline()
        if nextline == '' and pal_client_process.poll() is not None:
            break
        if len(str(nextline)) > 3:
            #This is where we process all the console outputs
            #check if we've already started the game
            if game_started:
                #checks during a running tournament
                analyze_line(nextline)
            else:
                #check to see if we can run the START command
                if "[Client thread/INFO] [polycraft]: Minecraft finished loading" in str(nextline):
                    #MInecraft has loaded and we can run the start command. First start up our thread
                    tm_thread = TournamentManager.TournamentThread(queue=queue, tm_lock=tm_lock)
                    tm_thread.start()
                    tm_thread.queue.put("START")

            sys.stdout.write(str(nextline) + '\n')
            sys.stdout.flush()

    output = pal_client_process.communicate()[0]
    exitCode = pal_client_process.returncode

    if (exitCode == 0):
        return output
    else:
        raise subprocess.CalledProcessError(exitCode, command)
    # popen = subprocess.Popen(cmd, cwd='../', stdout=subprocess.PIPE, universal_newlines=True, shell=True)
    # for stdout_line in iter(popen.stdout.readline, ""):
    #     yield stdout_line
    # popen.stdout.close()
    # return_code = popen.wait()
    # if return_code:
    #     raise subprocess.CalledProcessError(return_code, cmd)


def analyze_line(line):
    return None


def experiment_ended(line):
    return None


# def main():
#     #run polycraft client
#     print("test")
#     #execute("cd ..")
#     print("test")
#     print("test")


if __name__ == "__main__":
    execute("call gradlew runclient")


