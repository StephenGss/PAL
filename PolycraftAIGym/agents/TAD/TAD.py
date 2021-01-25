"""
Test Agent Deployment (TAD)
Author: Stephen Goss
Desc: TAD is a rule-based agent designed for testing purposes of PAL tasks
"""
import datetime
import getopt
import os
import socket
import queue
import json
import enum
import sys
import time

class Task(enum.Enum):
    Observe = 0
    MoveToBlock = 1
    BreakBlock = 2
    CraftItem = 3
    TreeTap = 4

class HLTask(enum.Enum):
    Start = 0
    CollectResources = 1
    Craft = 2
    WaitForEnd = 3

class TAD:

    def __init__(self, log_dir='Logs/', args=(), kwargs=None):
        self.games = 1000
        self.pal_host = '127.0.0.1'
        self.pal_port = 9000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tournament_over = False
        self.reset_all()
        if 'PAL_AGENT_PORT' in os.environ:
            self.pal_port = int(os.environ['PAL_AGENT_PORT'])
            print('Using Port: ' + os.environ['PAL_AGENT_PORT'])

    def reset_all(self):
        self.obs = {}
        self.recipes = {}
        self.position = [0, 0, 0]
        self.hl_state = HLTask.Start
        self.state = Task.Observe
        self.state_data = {}
        self.cq = queue.Queue()
        self.game_over = False
        self.inventory_by_slot = {}
        self.inventory_by_item = {}
        self.trees = []
        self.crafting_tables = []
        self.state_data.setdefault('broke_block', False)
        self.state_data.setdefault('block', 'minecraft:log')
        self.action_count = 0

    def send_command(self, command):
        """ function that enable the communication with PAL """
        print(command)
        sys.stdout.flush()
        # time.sleep(0.001)
        self.sock.send(str.encode(command + '\n'))
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = self.sock.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                # either 0 or end of data
                break
        # print(data)
        data_dict = json.loads(data)
        # print(data_dict)
        if 'gameOver' in data_dict:
            if data_dict['gameOver']:
                check_gameOver = True
                self.reset_all()
                print("Game Over flag detected")
        return data_dict

    def sense_all(self):
        self.action_count += 1
        return self.send_command("SENSE_ALL NONAV")

    def sense_screen(self):
        self.action_count += 1
        return self.send_command("SENSE_SCREEN")

    def update_obs(self):
        self.inventory_by_item.clear()
        self.inventory_by_slot.clear()
        self.trees.clear()
        self.crafting_tables.clear()

        # sense_screen for speed testing
        if screen:
            self.sense_screen()

        self.obs = self.sense_all()
        for slot in self.obs['inventory']:
            if str(slot).isdigit():
                slot = str(slot)
                if slot in self.inventory_by_slot.keys():
                    continue  # this shouldn't happen
                else:
                    self.inventory_by_slot.setdefault(slot, {str(self.obs['inventory'][slot]['item']), int(self.obs['inventory'][slot]['count'])})
                if self.obs['inventory'][slot]['item'] in self.inventory_by_item:
                    self.inventory_by_item[self.obs['inventory'][slot]['item']] += int(self.obs['inventory'][slot]['count'])
                else:
                    self.inventory_by_item.setdefault(str(self.obs['inventory'][slot]['item']), int(self.obs['inventory'][slot]['count']))
        self.position = self.obs['player']['pos']
        for block in self.obs['map']:
            if str(self.obs['map'][block]['name']).startswith('minecraft:log'):
                self.trees.append(str(block))
            if str(self.obs['map'][block]['name']).startswith('minecraft:crafting_table'):
                self.crafting_tables.append(str(block))

    def update_rec(self):
        self.recipes = self.send_command("SENSE_RECIPES");

    def move_towards(self, pos):
        response = self.send_command("MOVE w")
        if 'command_result' in response and 'result' in response['command_result'] and str(response['command_result']['result']).startswith('SUCCESS'):
            self.cq.put(lambda: self.move_towards(pos=pos))

    def plan(self):
        self.update_obs()

        # check for Game over
        if str(self.obs['gameOver']).startswith('true'):
            self.reset_all()
            self.update_obs()
            return

        if str(self.obs['goal']['goalAchieved']).lower().startswith('true'):
            print("SUCCEEDED")
            self.reset_all()
            self.update_obs()
            return

        # start by observing three times to make sure the exp is ready
        if self.hl_state == HLTask.Start:
            if self.action_count < 3:
                print('starting observations...')
                self.cq.put(lambda: self.update_obs())
            else:
                print('begin collecting resources')
                self.hl_state = HLTask.CollectResources
                self.state = Task.MoveToBlock
                self.state_data['block'] = 'minecraft:log'
        # break trees until we have 3 logs
        if self.hl_state == HLTask.CollectResources:
            if self.inventory_by_item.get('minecraft:log') is not None and self.inventory_by_item.get('minecraft:log') >= 3:
                print('finished collecting resources')
                self.hl_state = HLTask.Craft
                self.state = Task.MoveToBlock
                self.state_data['block'] = 'minecraft:crafting_table'
                return
            if self.state == Task.MoveToBlock:
                if str(self.obs['blockInFront']['name']).startswith('minecraft:log'):
                    print('found block. Attempt to break')
                    self.state = Task.BreakBlock
                    self.state_data['broke_block'] = False
                    if 'minecraft:log' in self.inventory_by_item.keys():
                        self.state_data['result_count'] = self.inventory_by_item.get('minecraft:log') + 1
                    else:
                        self.state_data.setdefault('result_count', 1)
                else:
                    self.cq.put(lambda: self.send_command(F"TP_TO {self.trees.pop()}"))
            if self.state == Task.BreakBlock:
                if not self.state_data['broke_block']:
                    if not str(self.obs['blockInFront']['name']).startswith('minecraft:log'):
                        return
                    self.cq.put(lambda: self.send_command(F"BREAK_BLOCK"))
                    self.cq.put(lambda: self.send_command("MOVE w"))
                    self.state_data['broke_block'] = True
                    self.state_data.setdefault('time_out_counter', 5)
                else:
                    print('waiting for block pickup')
                    if self.inventory_by_item.get('minecraft:log') == self.state_data.get('result_count'):
                        self.state = Task.MoveToBlock
                        self.state_data['time_out_counter'] -= 1
                    if self.state_data['time_out_counter'] <= 0:
                        self.state_data['broke_block'] = False
        if self.hl_state == HLTask.Craft:
            if self.state == Task.MoveToBlock:
                if str(self.state_data.get('block')).startswith('minecraft:crafting_table'):
                    self.cq.put(lambda: self.send_command(F"TP_TO {self.crafting_tables.pop()}"))
                else:
                    self.cq.put(lambda: self.send_command(F"TP_TO {self.trees.pop()} 2"))
                    self.state = Task.TreeTap
                    return
                self.state = Task.CraftItem
            if self.state == Task.CraftItem:
                if str(self.obs['blockInFront']['name']).startswith('polycraft:tree_tap'):
                    self.cq.put(lambda: self.send_command(F"TP_TO {self.crafting_tables.pop()}"))
                    self.cq.put(lambda: self.send_command(
                        F"craft 1 minecraft:stick minecraft:stick minecraft:stick minecraft:planks minecraft:stick minecraft:planks 0 polycraft:sack_polyisoprene_pellets 0"))
                    self.hl_state = HLTask.WaitForEnd
                self.cq.put(lambda: self.send_command(F"craft 1 minecraft:log 0 0 0"))
                self.cq.put(lambda: self.send_command(F"craft 1 minecraft:log 0 0 0"))
                self.cq.put(lambda: self.send_command(F"craft 1 minecraft:log 0 0 0"))
                self.cq.put(lambda: self.send_command(F"craft 1 minecraft:planks 0 minecraft:planks 0"))
                self.cq.put(lambda: self.send_command(F"craft 1 minecraft:planks 0 minecraft:planks 0"))
                self.cq.put(lambda: self.send_command(F"craft 1 minecraft:planks minecraft:stick minecraft:planks minecraft:planks 0 minecraft:planks 0 minecraft:planks 0"))
                self.state = Task.MoveToBlock
                self.state_data['block'] = 'minecraft:log'
                return
            if self.state == Task.TreeTap:
                self.cq.put(lambda: self.send_command(F"PLACE_TREE_TAP"))
                self.cq.put(lambda: self.send_command(F"EXTRACT_RUBBER"))
                self.state = Task.CraftItem
        if self.hl_state == HLTask.WaitForEnd:
            return

        # if 'blockInFront' in self.obs and str(self.obs['blockInFront']['name']).startswith("minecraft:air"):
        #     self.state = Task.MoveToBlock
        #     self.cq.put(lambda: self.move_towards(None))

    def plan_speed(self):
        for x in range(100):
            if screen:
                self.cq.put(lambda: self.sense_screen())
            self.cq.put(lambda: self.send_command(F"move w"))
            self.cq.put(lambda: self.send_command(F"move x"))
        if once:
            self.cq.put('exit')
        else:
            self.cq.put(lambda: self.send_command(F"GIVE_UP"))

    def execute(self, run_mode=None):
        self.sock.connect((self.pal_host, self.pal_port))

        while not self.game_over:
            if self.cq.empty():
                if run_mode == 'normal':
                    self.plan()
                else:
                    self.plan_speed()
            else:
                act = self.cq.get()
                if act == 'exit':
                    return
                act()
                self.action_count += 1

    def act_observe(self, time_out=5):
        self.cq.put(lambda: self.update_obs())
        self.cq.put(lambda: self.update_obs())

    def act_move_to_block(self, time_out=5):
        self.cq.put(lambda: self.move_towards())


if __name__ == "__main__":
    mode = 'normal'
    once = False
    screen = False

    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "hm:o:s:",
                                   ["mode=", "once=", "screen="])
    except getopt.GetoptError:
        print('TAD.py -m <mode> -o <run_once:True/False>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(
                'TAD.py -m <mode> -o <run_once:True/False>')
            sys.exit()
        elif opt in ("-m", "--mode"):
            mode = str(arg)
        elif opt in ("-o", "--once"):
            once = bool(arg)
        elif opt in ("-s", "--screen"):
            screen = bool(arg)

    startTime = datetime.datetime.now()

    tad = TAD()
    tad.execute(run_mode=mode)

    endTime = datetime.datetime.now()
    timeDiff = endTime - startTime
    ms = (timeDiff.microseconds / 1000) + timeDiff.seconds * 1000
    print("Time Taken: " + str(ms) + "ms")
    print("FPS: " + str(tad.action_count / (ms / 1000)))
