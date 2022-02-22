import numpy
import math
import traceback
import random
import time
import socket
import json
import os


class HugaPlanner:
    """
    Planner agent for HUGA Task in PAL
    """

    def __init__(self):
        # connect to socket'
        self.HOST = '127.0.0.1'
        self.PORT = 9000
        if 'PAL_PORT' in os.environ:
            self.PORT = int(os.environ['PAL_PORT'])
            print('Using Port: ' + os.environ['PAL_PORT'])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.HOST, self.PORT))
        self.check_goal_achieved = False
        self.check_gameOver = False

        # VIEW_MATRIX(map)
        self.map = numpy.repeat(-1, 200 * 200)
        self.map = self.map.reshape(200, 200)
        self.map_small = []
        self.map_side_x = 16
        self.map_side_z = 16

        self.big_map_to_show = numpy.repeat(-1, 200 * 200)
        self.big_map_to_show = self.big_map_to_show.reshape(200, 200)

        # set plot size and will stay this size
        # self.plt.rcParams['figure.figsize'] = (3, 3)

        self.key_num = 0
        self.has_Macguffin = False

        self.bot_pos = [0, 0]
        self.ini_pos = [0, 0]
        self.dog_pos = [0, 0]
        self.mac_pos = [0, 0]
        self.archway_pos = [0, 0]
        self.locked_door_pos = [0, 0]
        self.last_5_pos = []    # last 5 bot positions. Used to not go through pathway that was just used
        self.chest_pos = [0,0]
        self.checked_chest_pos = []
        self.all_chest_pos = []

        self.is_archway = False
        self.is_LockedDoor = False
        self.is_Macguffin = False
        self.is_LockedDoor_Room = False
        self.is_door_open = False
        self.is_Dog = False
        self.dog_tag = 0
        self.dog_steps = 0

        self.facing = 'NORTH'
        self.inv = {}
        self.doors = {}

        self.archway_candidates = []
        self.unexplored_archway_candidates = []
        self.archway_to_des_candidates = []

        self.obj_codes = {
            'minecraft:dirt': 3,
            'minecraft:log': 17,
            'minecraft:planks': 5,
            'minecraft:stick': 280,
            'minecraft:crafting_table': 58,
            'minecraft:wood_axe': 271,
            'minecraft:chest': 54,
            'minecraft:diamond_ore': 56,
            'minecraft:diamond_block': 57,
            'minecraft:diamond': 264,
            'minecraft:iron_pickaxe': 257,
            'minecraft:wooden_door': 64,
            'minecraft:sapling': 6,

            'polycraft:wooden_pogo_stick': 5989,
            'polycraft:tree_tap': 6321,
            'polycraft:bag_polyisoprene_pellets': 5398,
            'polycraft:sack_polyisoprene_pellets': 5399,
            'polycraft:powder_keg_polyisoprene_pellets': 5400,
            'polycraft:block_of_platinum': 5401,
            'polycraft:block_of_titanium': 5402,
            'polycraft:plastic_chest': 5403,
            'polycraft:key': 5000,
            'polycraft:safe': 5001,

            'polycraft:expblock': 5500,
            'polycraft:tier_chest': 5501,
            'polycraft:trap': 5502,
            'polycraft:macguffin': 5503,
            'polycraft:locked_door': 5504,

            '': -1
        }

        self.actions = {
            1: ['GET_BLOCK(object=17)'],  # get wood block
            2: ['CRAFT(5)'],  # craft planks
            3: ['CRAFT(280)'],  # craft sticks
            4: ['GET_RUBBER()'],  # create tree tap, place it and collect rubber
            5: ['CRAFT(57)'],  # craft diamond block
            6: ['CRAFT(58)', 'PLACE_BLOCK(58,FIND_NEAREST(object=0))'],  # craft crafting table
            7: ['GET_BLOCK(object=56)'],  # get diamonds from block
            8: ['GET_BLOCK(object=5401)'],  # get Pl block
            9: ['PLUNDER_SAFE()'],  # get blue key, open safe, get diamonds
            10: ['TRADE( material = "polycraft:block_of_platinum",quantity = 1 )'],  # trade Pl block for Ti block
            11: ['TRADE( material = "minecraft:log",quantity = 10 )'],  # trade wood log block for Ti block
            12: ['TRADE( material = "polycraft:block_of_platinum",quantity = 2 )'],  # trade 2 Ti blocks for 9 diamonds

            15: ['CRAFT(5989)']  # craft diamond Ti pogo stick
        }

    def VIEW_MATRIX(self, m):
        "to visualize a matrix in all its glory"
        import sys
        import numpy
        numpy.set_printoptions(threshold=sys.maxsize)
        print(m)

    def RESET(self):
        agent.check_gameOver = False
        agent.check_goal_achieved = False

        self.map = numpy.repeat(-1, 200 * 200)
        self.map = self.map.reshape(200, 200)
        self.map_small = []
        self.map_side_x = 16
        self.map_side_z = 16

        self.big_map_to_show = numpy.repeat(-1, 200 * 200)
        self.big_map_to_show = self.big_map_to_show.reshape(200, 200)

        self.key_num = 0
        self.has_Macguffin = False

        self.bot_pos = [0, 0]
        self.ini_pos = [0, 0]
        self.dog_pos = [0, 0]
        self.mac_pos = [0, 0]
        self.archway_pos = [0, 0]
        self.locked_door_pos = [0, 0]
        self.chest_pos = [0,0]
        self.checked_chest_pos = []
        self.all_chest_pos = []

        self.is_archway = False
        self.is_LockedDoor = False
        self.is_Macguffin = False
        self.is_LockedDoor_Room = False
        self.is_Dog = False
        self.dog_tag = 0
        self.dog_steps = 0

        self.facing = 'NORTH'
        self.inv = {}
        self.doors = {}

        self.archway_candidates = []
        self.archway_to_des_candidates = []

    def UPDATE(self, obs):

        # self.map_small

        self.bot_pos = [obs['player']['pos'][0], obs['player']['pos'][2]]  # matrix coordenates

        # keep track of last 5 positions. This is so we don't go back through a pathway we just went through
        self.last_5_pos.insert(0, [obs['player']['pos'][0], obs['player']['pos'][2]])
        if len(self.last_5_pos) > 12:
            del self.last_5_pos[-1]
        self.facing = obs['player']['facing']
        self.doors = {}

        self.is_Dog = False
        self.is_LockedDoor = False
        self.is_Macguffin = False
        self.is_archway = False
        self.is_LockedDoor_Room = False
        self.is_door_open = False

        if 'name' in obs['blockInFront'] and obs['blockInFront']['name'] == 'polycraft:locked_door':
            self.is_door_open = str(obs['blockInFront']['open']).lower() in ['true']

        # i nv = numpy.array([[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]])
        # inv.shape
        invent = {}
        self.key_num = 0
        for i in obs['inventory']:
            # print(i)
            # inv = numpy.vstack([inv,[int(i), obs['inventory'][i],0,0,0,-1,1]])
            invent[str(self.obj_codes[obs['inventory'][i]['item']])] = obs['inventory'][i]['count']
            if i != 'selectedItem' and obs['inventory'][i]['item'] == 'polycraft:key':
                self.key_num += 1
            if i != 'selectedItem' and obs['inventory'][i]['item'] == 'polycraft:macguffin':
                self.has_Macguffin = True

        self.inv = invent.copy()
        # self.map_small = numpy.array(obs['map']['blocks'])
        map_list = obs['map']['blocks'].copy()
        map_to_show = numpy.copy(map_list)
        self.map_side_x = obs['map']['size'][0]  # int((len(map_list))**(1/2))
        self.map_side_z = obs['map']['size'][2]  # int((len(map_list))**(1/2))

        chests_in_room = []

        for i in range(len(map_list)):
            if map_list[i] == 'polycraft:expblock':
                map_list[i] = self.obj_codes['polycraft:expblock']
                map_to_show[i] = 7
            if map_list[i] == 'minecraft:air':
                map_list[i] = 0
                map_to_show[i] = 0
            if map_list[i] == 'polycraft:tier_chest':
                map_list[i] = self.obj_codes['polycraft:tier_chest']
                map_to_show[i] = 6
                chest_pos_tmp = [math.floor(i/(obs['map']['size'][2])+obs['map']['origin'][0]), i % obs['map']['size'][2]+obs['map']['origin'][2]]
                if chest_pos_tmp not in self.all_chest_pos:
                    self.all_chest_pos.append(chest_pos_tmp)
                chests_in_room.append(chest_pos_tmp)
            if map_list[i] == 'minecraft:wooden_door':
                map_list[i] = self.obj_codes['minecraft:wooden_door']
                map_to_show[i] = 8
            if map_list[i] == 'polycraft:trap':
                map_list[i] = self.obj_codes['polycraft:trap']
                map_to_show[i] = 9
            if map_list[i] == 'polycraft:macguffin':
                map_list[i] = self.obj_codes['polycraft:macguffin']
                self.is_Macguffin = True
                map_to_show[i] = 12
            if map_list[i] == 'polycraft:locked_door':
                map_list[i] = self.obj_codes['polycraft:locked_door']
                map_to_show[i] = 13

        # set the nearest unchecked chest
        self.chest_pos = [0,0]
        chest_candidates = []
        # first check through chests in the current room
        for pos in chests_in_room:
            if pos in self.checked_chest_pos:
                continue
            else:
                chest_candidates.append(pos)
        if len(chest_candidates) == 0:
            for pos in self.all_chest_pos:
                if pos in self.checked_chest_pos:
                    continue
                else:
                    chest_candidates.append(pos)
        if len(chest_candidates) > 0:
            self.chest_pos = self.FIND_NEAREST(chest_candidates)


        self.map_small = numpy.copy(map_list)
        self.map_small = self.map_small.reshape((self.map_side_x, self.map_side_z))

        map_to_show = map_to_show.astype(numpy.float)
        map_to_show = map_to_show.reshape((self.map_side_x, self.map_side_z))

        for i in range(self.map_small.shape[0]):
            for j in range(self.map_small.shape[1]):
                self.map[obs['map']['origin'][0] + i, obs['map']['origin'][2] + j] = self.map_small[i, j]
                self.big_map_to_show[obs['map']['origin'][0] + i, obs['map']['origin'][2] + j] = map_to_show[i, j]
        for i in obs['entities']:
            # print(obs['entities'][i])
            if obs['entities'][i]['type'] == 'EntityPatrol':
                self.map[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2])] = 60000 + \
                                                                                                 obs['entities'][i][
                                                                                                     'id']
                self.big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2])] = 10
                if obs['entities'][i]['color'] == 'red':
                    self.big_map_to_show[int(obs['entities'][i]['pos'][0]) + 1, int(obs['entities'][i]['pos'][2])] = 10
                    self.big_map_to_show[int(obs['entities'][i]['pos'][0]) - 1, int(obs['entities'][i]['pos'][2])] = 10
                    self.big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2]) + 1] = 10
                    self.big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2]) - 1] = 10
                    self.big_map_to_show[
                        int(obs['entities'][i]['pos'][0]) + 1, int(obs['entities'][i]['pos'][2]) + 1] = 10
                    self.big_map_to_show[
                        int(obs['entities'][i]['pos'][0]) - 1, int(obs['entities'][i]['pos'][2]) - 1] = 10
                    self.big_map_to_show[
                        int(obs['entities'][i]['pos'][0]) - 1, int(obs['entities'][i]['pos'][2]) + 1] = 10
                    self.big_map_to_show[
                        int(obs['entities'][i]['pos'][0]) + 1, int(obs['entities'][i]['pos'][2]) - 1] = 10

        for i in obs['entities']:
            if obs['entities'][i]['type'] == 'EntityDog':
                self.is_Dog = True
                self.map[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2])] = 61000 + \
                                                                                                 obs['entities'][i][
                                                                                                     'id']
                self.big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2])] = 11
                self.dog_pos = [int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2])]
                self.dog_tag = i
        if (13 in self.big_map_to_show):
            self.is_LockedDoor = True
            locked_door_pos_to_show = numpy.where(self.big_map_to_show == 13)
            self.locked_door_pos = self.FIND_NEAREST_LOCKED(locked_door_pos_to_show)

        if not self.is_Dog:
            self.dog_pos = [0, 0]
        # if 11 in self.big_map_to_show:
        #     self.is_Dog = True
        #     self.dog_pos = numpy.where(self.big_map_to_show == 11)
        # self.map_small_ = self.map_small
        if self.is_Macguffin:
            mac_pos_to_show = numpy.where(map_to_show == 12)
            self.mac_pos = [obs['map']['origin'][0] + mac_pos_to_show[0][0],
                            obs['map']['origin'][2] + mac_pos_to_show[1][0]]

        for i in numpy.transpose(numpy.where(map == 5504)):
            print(i)
            self.doors[((i[0] - self.bot_pos[0]) ** 2 + (i[1] - self.bot_pos[1]) ** 2) ** (1 / 2)] = i
        # map_ = map
        zeros_coord = numpy.where((self.big_map_to_show == 0) | (self.big_map_to_show == 11))
        self.archway_candidates = []
        self.unexplored_archway_candidates = []
        self.archway_to_des_candidates = []
        for i in range(len(zeros_coord[0])):
            zero_candidate = [zeros_coord[0][i], zeros_coord[1][i]]
            if self.map[zero_candidate[0], zero_candidate[1]] == 0 \
                    and (self.map[zero_candidate[0] + 1, zero_candidate[1]] == -1
                         or self.map[zero_candidate[0] - 1, zero_candidate[1]] == -1
                         or self.map[zero_candidate[0], zero_candidate[1] + 1] == -1
                         or self.map[zero_candidate[0], zero_candidate[1] - 1] == -1):
                self.archway_candidates.append(zero_candidate)
                self.unexplored_archway_candidates.append(zero_candidate)
            if self.map[zero_candidate[0], zero_candidate[1]] == 0 \
                    and ((self.map[zero_candidate[0] + 1, zero_candidate[1]] == 5500
                          and self.map[zero_candidate[0] - 1, zero_candidate[1]] == 5500)
                         or (self.map[zero_candidate[0], zero_candidate[1] + 1] == 5500
                             and self.map[zero_candidate[0], zero_candidate[1] - 1] == 5500)) \
                    and zero_candidate not in self.last_5_pos:
                self.archway_candidates.append(zero_candidate)
            if self.map[zero_candidate[0], zero_candidate[1]] == 0 \
                    and (self.map[zero_candidate[0] + 1, zero_candidate[1]] != -1
                         and self.map[zero_candidate[0] - 1, zero_candidate[1]] != -1
                         and self.map[zero_candidate[0], zero_candidate[1] + 1] != -1
                         and self.map[zero_candidate[0], zero_candidate[1] - 1] != -1):
                self.archway_to_des_candidates.append(zero_candidate)
            if self.big_map_to_show[zero_candidate[0], zero_candidate[1]] == 11 \
                    and (self.map[zero_candidate[0] + 1, zero_candidate[1]] == -1
                         or self.map[zero_candidate[0] - 1, zero_candidate[1]] == -1
                         or self.map[zero_candidate[0], zero_candidate[1] + 1] == -1
                         or self.map[zero_candidate[0], zero_candidate[1] - 1] == -1):
                self.archway_candidates.append(zero_candidate)

        zeros_coord = numpy.where((self.big_map_to_show == 0))
        archway_to_des_candidates = self.archway_to_des_candidates.extend(self.archway_candidates)
        # Map plot
        if (len(self.archway_candidates) == 0):
            pass
        if len(self.unexplored_archway_candidates) > 0:
            self.archway_pos = self.FIND_NEAREST(self.unexplored_archway_candidates)
        else:
            self.archway_pos = self.FIND_NEAREST(self.archway_candidates)

    ########################################## Astar ###########################################################

    # map for Astar
    def map_to_string(self, map1):
        map_side1 = int(len(map1))
        map_for_Astar = str()
        for i in range(map1.shape[0]):
            for ii in range(map1.shape[1]):
                if map1[ii, i] == 0 or map1[ii, i] == 64 or map1[ii, i] == 12:
                    map_for_Astar = map_for_Astar + ' '
                else:
                    map_for_Astar = map_for_Astar + '+'
                if ii == map_side1 - 1:
                    map_for_Astar = map_for_Astar + '\n'
        return (map_for_Astar)

    # map_for_Astar = map_to_string(map)
    # print(map_for_Astar)

    def drawmaze(maze, set1=[], set2=[], c='#', c2='*'):
        """returns an ascii maze, drawing eventually one (or 2) sets of positions.
              useful to draw the solution found by the astar algorithm
          """
        set1 = list(set1)
        set2 = list(set2)
        lines = maze.strip().split('\n')
        width = len(lines[0])
        height = len(lines)
        result = ''
        for j in range(height):
            for i in range(width):
                if (i, j) in set1:
                    result = result + c
                elif (i, j) in set2:
                    result = result + c2
                else:
                    result = result + lines[j][i]
            result = result + '\n'
        return result

    # setting Astar
    from astar import AStar
    class MazeSolver(AStar):

        """sample use of the astar algorithm. In this exemple we work on a maze made of ascii characters,
            and a 'node' is just a (x,y) tuple that represents a reachable position"""

        def __init__(self, maze):
            self.lines = maze.strip().split('\n')
            self.width = len(self.lines[0])
            self.height = len(self.lines)

        def heuristic_cost_estimate(self, n1, n2):
            """computes the 'direct' distance between two (x,y) tuples"""
            (x1, y1) = n1
            (x2, y2) = n2
            return math.hypot(x2 - x1, y2 - y1)

        def distance_between(self, n1, n2):
            """this method always returns 1, as two 'neighbors' are always adajcent"""
            return 1

        def neighbors(self, node):
            """ for a given coordinate in the maze, returns up to 4 adjacent(south,southwest,west,northwest,north,northeast,east,southeast)
                        nodes that can be reached (=any adjacent coordinate that is not a wall)
                  """
            x, y = node
            if self.lines[y - 1][x] == ' ' and self.lines[y - 1][x - 1] == ' ' and self.lines[y][x - 1] == ' ' and \
                    self.lines[y + 1][x - 1] == ' ' and self.lines[y + 1][x] == ' ' and self.lines[y + 1][
                x + 1] == ' ' and self.lines[y][x + 1] == ' ' and self.lines[y - 1][x + 1] == ' ':
                return [(nx, ny) for nx, ny in
                        [(x, y - 1), (x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1), (x + 1, y),
                         (x + 1, y - 1)] if
                        0 <= nx < self.width and 0 <= ny < self.height and self.lines[ny][nx] == ' ']
            else:
                return [(nx, ny) for nx, ny in [(x, y - 1), (x - 1, y), (x, y + 1), (x + 1, y)] if
                        0 <= nx < self.width and 0 <= ny < self.height and self.lines[ny][nx] == ' ']

    ###############################################################################################################################################

    def WALK_TO(self, new_pos):
        "WALK_TO function, go to new_pos, avoiding objects, stay in matrix, stop near an ocopied possition"

        temp_pos = self.bot_pos.copy()  # map coordenates [x,z]

        try:
            if (self.map[new_pos[0], new_pos[1]] == -1 or self.map[
                new_pos[0], new_pos[1]] == 7):
                print('test')
        except TypeError as e:
            # print(e)
            observation = self.MC('SENSE_ALL')
            self.UPDATE(obs=observation)
            return

        if (self.map[new_pos[0], new_pos[1]] == -1 or self.map[
            new_pos[0], new_pos[1]] == 7):  # verify if the new position is not within the map
            print('Destination out of the world')

        else:
            if (self.map[new_pos[0], new_pos[1]] != 0):  # if destination in occupied
                free_places = numpy.array(numpy.where(
                    (self.big_map_to_show == 0) | (
                            self.big_map_to_show == 12)))  # matrix coordenates [z,x] | find free places
                free_places = numpy.vstack((free_places, [0] * free_places.shape[1]))
                free_places.shape
                for i in range(free_places.shape[1]):
                    free_places[2, i] = ((free_places[0, i] - new_pos[0]) ** 2 + (
                            free_places[1, i] - new_pos[1]) ** 2) ** (1 / 2)  # distance of new_pos to free places

                free_places_close = numpy.where(free_places[2, :] == numpy.min(free_places[2, :]))[
                    0]  # choose the closest free place
                ##len(free_places_close)

                if (len(free_places_close) == 1):  # if closest free place is just one
                    new_pos = free_places[0:2, free_places_close].transpose().tolist()[
                        0]  # matrix coordenates [z,x] | choose it as the new new_pos
                else:  # if not, choose the one closest to the bot
                    free_places_close = free_places[0:2,
                                        free_places_close].transpose().tolist()  # matrix coordenates [z,x]
                    ##########check if the 4 nearest neighbors are occupied
                    free_places_close_new = []
                    for i in range(len(free_places_close)):
                        if (self.big_map_to_show[free_places_close[i][0] + 1, free_places_close[i][1]] == 0 or
                                self.big_map_to_show[free_places_close[i][0] - 1, free_places_close[i][1]] == 0 or
                                self.big_map_to_show[free_places_close[i][0], free_places_close[i][1] + 1] == 0 or
                                self.big_map_to_show[free_places_close[i][0], free_places_close[i][1] - 1] == 0):
                            free_places_close_new.append(free_places_close[i])

                    if self.big_map_to_show[new_pos[0], new_pos[1]] == 13:
                        free_places_dist_to_door = [0] * len(free_places_close_new)
                        for ii in range(len(free_places_close_new)):
                            free_places_dist_to_door[ii] = ((free_places_close_new[ii][0] - new_pos[0]) ** 2 + (
                                    free_places_close_new[ii][1] - new_pos[1]) ** 2)

                        new_pos = free_places_close_new[
                            numpy.where(free_places_dist_to_door == numpy.min(free_places_dist_to_door))[0][
                                0]]  # matrix coordenates [z,x]
                        new_pos = [new_pos[0], new_pos[1]]
                    elif self.is_archway == True:
                        free_places_dist_to_door = [0] * len(free_places_close_new)
                        for ii in range(len(free_places_close_new)):
                            free_places_dist_to_door[ii] = ((free_places_close_new[ii][0] - new_pos[0]) ** 2 + (
                                    free_places_close_new[ii][1] - new_pos[1]) ** 2)

                        new_pos = free_places_close_new[
                            numpy.where(free_places_dist_to_door == numpy.min(free_places_dist_to_door))[0][
                                0]]  # matrix coordenates [z,x]
                        new_pos = [new_pos[0], new_pos[1]]
                    else:
                        free_places_dist_to_bot = [0] * len(free_places_close_new)
                        for ii in range(len(free_places_close_new)):
                            free_places_dist_to_bot[ii] = ((free_places_close_new[ii][0] - self.bot_pos[0]) ** 2 + (
                                    free_places_close_new[ii][1] - self.bot_pos[1]) ** 2) ** (1 / 2)

                        new_pos = free_places_close_new[
                            numpy.where(free_places_dist_to_bot == numpy.min(free_places_dist_to_bot))[0][
                                0]]  # matrix coordenates [z,x]
                        new_pos = [new_pos[0], new_pos[1]]  # map coordenates

            if (self.bot_pos == new_pos):  # if the new_pos is equal to the self.bot_pos, the bot is there already
                print('Already there')
            else:
                counter = 0
                while (self.bot_pos != new_pos):
                    # Astar #
                    start = tuple(self.bot_pos)  # we choose to start at the upper left corner
                    goal = tuple(new_pos)  # we want to reach the lower right corner
                    map_for_Astar = self.map_to_string(self.big_map_to_show)
                    test = self.MazeSolver(map_for_Astar).astar(start, goal)
                    foundPath = []
                    if test is None:
                        self.MC('NOP')
                        observation = self.MC('SENSE_ALL')
                        self.UPDATE(obs=observation)
                        if self.bot_pos == self.ini_pos:
                            return
                        # if abs(self.bot_pos[0] - new_pos[0]) > self.map_side_x or abs(
                        #         self.bot_pos[1] - new_pos[1]) > self.map_side_z\
                        #         or self.bot_pos == self.ini_pos:
                        #     self.WALK_TO_NEXT_ROOM()

                        if foundPath is not None and len(foundPath) > 2:
                            # test = self.MazeSolver(map_for_Astar).astar(start, foundPath[-2])
                            new_pos = list(foundPath[-2])
                        # if test is None:
                        counter += 1
                        if counter >= 10:
                            return
                        continue

                    foundPath = list(test)  # let's solve it

                    # print(drawmaze(map_for_Astar, list(foundPath)))                   # print the solution to verify
                    if len(foundPath) == 1 or len(foundPath) == 0:
                        self.MC('NOP')
                        observation = self.MC('SENSE_ALL')
                        self.UPDATE(obs=observation)
                        if self.bot_pos == self.ini_pos:
                            self.WALK_TO(temp_pos)

                        continue

                    i = 0
                    move = numpy.subtract(foundPath[i + 1], foundPath[i])
                    if sum(move == [1, 0]) == 2:
                        self.MC('MOVE_EAST')
                    elif sum(move == [1, 1]) == 2:
                        self.MC('LOOK_SOUTH')
                        self.MC('SMOOTH_MOVE Q')
                    elif sum(move == [0, 1]) == 2:
                        self.MC('MOVE_SOUTH')
                        self.MC('SENSE_ALL')
                    elif sum(move == [-1, 1]) == 2:
                        self.MC('LOOK_SOUTH')
                        self.MC('SMOOTH_MOVE E')
                    elif sum(move == [-1, 0]) == 2:
                        self.MC('MOVE_WEST')
                    elif (sum(move == [-1, -1]) == 2):
                        self.MC('LOOK_NORTH')
                        self.MC('SMOOTH_MOVE Q')
                    elif (sum(move == [0, -1]) == 2):
                        self.MC('MOVE_NORTH')
                        self.MC('SENSE_ALL')
                    elif (sum(move == [1, -1]) == 2):
                        self.MC('LOOK_NORTH')
                        self.MC('SMOOTH_MOVE E')
                    observation = self.MC('SENSE_ALL')
                    self.UPDATE(observation)
                    if self.is_Macguffin:
                        self.WALK_TO(self.mac_pos)
                        self.has_Macguffin = True
                        observation = self.MC('SENSE_ALL')
                        self.UPDATE(obs=observation)


    def FIND_NEAREST(self, object):
        "Find nearest object in the map relative to the bot"
        # Objects = numpy.where(map==object)                     # find the objects in the map
        Objects = object
        if (len(Objects) == 0):
            print('NO such object present on map.')
            return (19760429)
        else:
            Objects_dist_to_bot = [0] * len(Objects)  # create a column to store the Euclidian distances
            for i in range(len(Objects)):
                # calculate the Euclidian distances of the objects to the player
                Objects_dist_to_bot[i] = ((Objects[i][0] - self.bot_pos[0]) ** 2 + (
                        Objects[i][1] - self.bot_pos[1]) ** 2) ** (
                                                 1 / 2)

            # find the object that is at the minimum distance
            aux = numpy.where(Objects_dist_to_bot == numpy.min(Objects_dist_to_bot))[0][0]
            Object = [Objects[aux][0], Objects[aux][1]]
            return (Object)

    def FIND_NEAREST_LOCKED(self, object):
        "Find nearest object in the map relative to the bot"
        # Objects = numpy.where(map==object)                     # find the objects in the map
        Objects = object
        if (len(Objects) == 0):
            print('NO such object present on map.')
            return (19760429)
        else:
            Objects_dist_to_bot = [0] * len(Objects[0])  # create a column to store the Euclidian distances
            for i in range(len(Objects[0])):
                # calculate the Euclidian distances of the objects to the player
                Objects_dist_to_bot[i] = ((Objects[0][i] - self.bot_pos[0]) ** 2 + (
                        Objects[1][i] - self.bot_pos[1]) ** 2) ** (
                                                 1 / 2)

            # find the object that is at the minimum distance
            aux = numpy.where(Objects_dist_to_bot == numpy.min(Objects_dist_to_bot))[0][0]
            Object = [Objects[0][aux], Objects[1][aux]]
            return (Object)

    # FIND_NEAREST(object=17)
    # object = object +60000

    def FIND_PLACE_NEARBY(self, pos):
        "Find a place in one of the four cardinal squares near a position"
        cardinal_pos = [(pos[0] + 1, pos[1]), (pos[0], pos[1] + 1), (pos[0] - 1, pos[1]), (pos[0], pos[1] - 1)]
        random.shuffle(cardinal_pos)
        cardinal_dist_bot = []
        to_remove = []
        for i in cardinal_pos:
            if self.map[i] == 0:
                cardinal_dist_bot.append(((i[0] - self.bot_pos[0]) ** 2 + (i[1] - self.bot_pos[1]) ** 2) ** (1 / 2))
            else:
                to_remove.append(i)
        for ii in to_remove:
            cardinal_pos.remove(ii)
        return list(cardinal_pos[numpy.where(cardinal_dist_bot == numpy.min(cardinal_dist_bot))[0][0]])

    # FIND_PLACE_NEARBY([50,40])

    def TURN_TO(self, obj_pos):
        obs = self.MC('SENSE_ALL')
        self.UPDATE(obs)
        if obj_pos[0] - self.bot_pos[0] == 1 and obj_pos[1] - self.bot_pos[1] == 0:
            obs = self.MC('LOOK_EAST')
            facing = 'EAST'
        if obj_pos[0] - self.bot_pos[0] == -1 and obj_pos[1] - self.bot_pos[1] == 0:
            obs = self.MC('LOOK_WEST')
            facing = 'WEST'
        if obj_pos[0] - self.bot_pos[0] == 0 and obj_pos[1] - self.bot_pos[1] == -1:
            obs = self.MC('LOOK_NORTH')
            facing = 'NORTH'
        if obj_pos[0] - self.bot_pos[0] == 0 and obj_pos[1] - self.bot_pos[1] == 1:
            obs = self.MC('LOOK_SOUTH')
            facing = 'SOUTH'

        return obs

    # TURN_TO(obj_pos = [50,40])      # LOOK_east

    def WALK_TO_NEXT_ROOM(self):
        temp_pos = self.bot_pos
        "Walk to the dog, interacts with it, follows it and retrive the key from the safe."
        self.is_archway = True
        # if dog_pos == [0,0]:
        # dog_pos = archway_pos
        self.WALK_TO(self.archway_pos)

        # TURN_TO(archway_pos)

    def WALK_TO_LOCKED_DOOR(self):
        temp_pos = self.bot_pos
        "Walk to the dog, interacts with it, follows it and retrive the key from the safe."
        # if dog_pos == [0,0]:
        # dog_pos = archway_pos
        self.WALK_TO(self.locked_door_pos)
        self.TURN_TO(self.locked_door_pos)

    def UNLOCK_DOOR(self):
        self.UPDATE(obs=self.MC('SENSE_ALL'))
        # open the door if it is closed
        if not self.is_door_open:
            for a in observation['inventory']:
                if observation['inventory'][a]['item'] == 'polycraft:key':
                    self.MC('SELECT_ITEM polycraft:key' + ' ' + str(observation['inventory'][a]['damage']))
                    # self.MC('SELECT_ITEM polycraft:macguffin')
                    # observation['inventory']['selectedItem']['damage'] = observation['inventory'][a]['damage']
                    # observation['inventory']['selectedItem']['slot'] = a
                    result = self.MC('USE')
                    if result['command_result']['result'] == 'SUCCESS':
                        break

        self.MC('move w')
        # self.MC('move w')

    def WALK_TO_DES(self):
        temp_pos = self.bot_pos
        self.WALK_TO([observation['destinationPos'][0], observation['destinationPos'][2]])

        # self.MC('PLACE_MACGUFFIN')

    def GET_KEY(self):
        "Walk to the dog, interacts with it, follows it and retrive the key from the safe."
        # if dog_pos == [0,0]:
        # dog_pos = archway_pos
        attempts = 0
        while self.dog_pos == [0, 0]:
            self.WALK_TO_NEXT_ROOM()
            self.MC('move w')
            self.UPDATE(obs=self.MC('SENSE_ALL'))
            attempts += 1
            if attempts >= 5:
                # too many attempts. refresh memory
                temp = self.ini_pos
                self.RESET()
                self.ini_pos = temp
                attempts = 0

        temp_pos = self.bot_pos
        self.WALK_TO(self.dog_pos)
        self.MC("interact " + self.dog_tag)

        dog_pos_list = [[1, 1], [2, 2], self.dog_pos]
        self.bot_pos_tminus1 = self.bot_pos
        nop_count = 0
        while (dog_pos_list[2] != dog_pos_list[1] or dog_pos_list[1] != dog_pos_list[0]) or not (
                self.map[self.dog_pos[0] - 1, self.dog_pos[1]] == 5501 or self.map[
            self.dog_pos[0], self.dog_pos[1] - 1] == 5501 or self.map[
                    self.dog_pos[0] + 1, self.dog_pos[1]] == 5501 or self.map[
                    self.dog_pos[0], self.dog_pos[1] + 1] == 5501):
            temp_pos = self.bot_pos
            self.WALK_TO(new_pos=self.dog_pos)
            self.UPDATE(obs=self.MC('SENSE_ALL'))
            """
                  if is_Macguffin:
                        WALK_TO(self.mac_pos)
                        has_Macguffin = True
                        observation = self.MC('SENSE_ALL')
                        UPDATE(obs=observation)
                  """
            if self.bot_pos == self.bot_pos_tminus1:
                self.MC("NOP")
                nop_count += 1
                if nop_count > 10:
                    self.MC("Move w")
                    if self.key_num == 3:
                        return

            self.UPDATE(obs=self.MC('SENSE_ALL'))
            if self.bot_pos == self.ini_pos:
                self.WALK_TO(temp_pos)

            attempts = 0
            while self.dog_pos == [0, 0]:
                observation = self.MC('SENSE_ALL')
                self.UPDATE(obs=observation)
                self.WALK_TO_NEXT_ROOM()
                self.MC('move w')
                observation = self.MC('SENSE_ALL')
                self.UPDATE(obs=observation)
                attempts += 1
                if attempts >= 5:
                    # too many attempts. refresh memory
                    temp = self.ini_pos
                    self.RESET()
                    self.ini_pos = temp
                    attempts = 0

            self.bot_pos_tminus1 = self.bot_pos
            dog_pos_list.append(self.dog_pos)
            dog_pos_list = dog_pos_list[1:4]

        safe_location = []
        if (self.map[self.dog_pos[0] - 1, self.dog_pos[1]] == 5501):
            safe_location.append([self.dog_pos[0] - 1, self.dog_pos[1]])
        if (self.map[self.dog_pos[0], self.dog_pos[1] - 1] == 5501):
            safe_location.append([self.dog_pos[0], self.dog_pos[1] - 1])
        if (self.map[self.dog_pos[0] + 1, self.dog_pos[1]] == 5501):
            safe_location.append([self.dog_pos[0] + 1, self.dog_pos[1]])
        if (self.map[self.dog_pos[0], self.dog_pos[1] + 1] == 5501):
            safe_location.append([self.dog_pos[0], self.dog_pos[1] + 1])
        for i in safe_location:
            if not ([self.bot_pos[0] - 1, self.bot_pos[1]] == i or [self.bot_pos[0], self.bot_pos[1] - 1] == i or [
                self.bot_pos[0] + 1,
                self.bot_pos[1]] == i or [
                        self.bot_pos[0], self.bot_pos[1] + 1] == i):
                temp_pos = self.bot_pos
                self.WALK_TO(list(self.FIND_PLACE_NEARBY(pos=i)))

            self.TURN_TO(obj_pos=i)
            result = self.MC("collect")
            if result['command_result']['result'] == 'SUCCESS':
                self.key_num += 1
                break
        observation = self.MC('SENSE_ALL')
        self.UPDATE(obs=observation)

    def GET_KEY_NO_DOG(self):
        """ Walk to next chest, try to collect """
        if self.chest_pos == [0, 0]:
            self.WALK_TO_NEXT_ROOM()
            self.MC('move w')
            self.UPDATE(obs=self.MC('SENSE_ALL'))

        temp_chest_pos = self.FIND_PLACE_NEARBY(self.chest_pos)
        self.WALK_TO(self.FIND_PLACE_NEARBY(self.chest_pos))
        self.TURN_TO(obj_pos=self.chest_pos)
        self.UPDATE(obs=self.MC('SENSE_ALL'))

        if self.face_offset(self.facing, self.bot_pos) == self.chest_pos:
            self.checked_chest_pos.append([self.chest_pos[0], self.chest_pos[1]])
            self.MC("collect")
            observation = agent.MC('SENSE_ALL')
            agent.UPDATE(obs=observation)

    def face_offset(self, face, pos):
        """ returns a position offset by one in the direction of face"""
        face = str(face).lower()
        if face == 'north':
            return [pos[0], pos[1] - 1]
        elif face == 'south':
            return [pos[0], pos[1] + 1]
        elif face == 'east':
            return [pos[0] + 1, pos[1]]
        elif face == 'west':
            return [pos[0] - 1, pos[1]]

    def GET_MAC(self):
        observation = self.MC('SENSE_ALL')
        self.UPDATE(obs=observation)

        if not self.has_Macguffin:

            while not is_Macguffin and not self.has_Macguffin:
                # WALK_TO(self.mac_pos)
                # has_Macguffin = True
                self.WALK_TO_NEXT_ROOM()
                self.MC('move w')
                # self.MC('move w')
                observation = self.MC('SENSE_ALL')
                self.UPDATE(obs=observation)
            if is_Macguffin:
                temp_pos = self.bot_pos
                self.WALK_TO(self.mac_pos)
                self.has_Macguffin = True
                observation = self.MC('SENSE_ALL')
                self.UPDATE(obs=observation)

    def GET_DES(self):
        if not self.is_LockedDoor:
            # WALK_TO(self.mac_pos)
            # has_Macguffin = True
            # WALK_TO(locked_door_pos)
            self.WALK_TO_NEXT_ROOM()
            self.MC('move w')
            self.MC('move w')
            # self.MC('move w')
            observation = self.MC('SENSE_ALL')
            self.UPDATE(obs=observation)
        if self.is_LockedDoor:
            self.UNLOCK_DOOR()
            self.WALK_TO_LOCKED_DOOR()
            self.UNLOCK_DOOR()
            self.MC('move w')

        self.MC('move w')
        observation = self.MC('SENSE_ALL')
        self.UPDATE(obs=observation)

        self.WALK_TO_DES()

    ######################################### Minecraft commands ################################################################

    def MC(self, command):
        "function that enable the communication with minecraft"
        print(command)
        self.sock.send(str.encode(command + '\n'))
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = self.sock.recv(BUFF_SIZE)
            data += part
            time.sleep(.001)
            if len(part) < BUFF_SIZE:
                # either 0 or end of data
                break
        print(data)
        data_dict = json.loads(data)
        # print(data_dict)
        if 'gameOver' in data_dict:
            if data_dict['gameOver']:
                self.RESET()
                self.check_gameOver = True
                print("Game Over flag detected")

        self.check_goal_achieved = False
        if 'goal' in data_dict and 'goalAchieved' in data_dict['goal']:
            if data_dict['goal']['goalAchieved']:
                self.RESET()
                self.check_goal_achieved = True
                print("Goal achieved!")
        return data_dict


if __name__ == "__main__":
    PYDEV_DEBUG = True
    time.sleep(3)
    agent = HugaPlanner()

    game = 1
    while game < 100 + 1:
        try:
            key_num = 0
            has_Macguffin = False
            agent.check_gameOver = False
            agent.check_goal_achieved = False
            # reset map update
            map = numpy.repeat(-1, 200 * 200)
            map = map.reshape(200, 200)

            agent.big_map_to_show = numpy.repeat(-1, 200 * 200)
            agent.big_map_to_show = agent.big_map_to_show.reshape(200, 200)

            # plt.close() # close plot

            observation = agent.MC('SENSE_ALL')
            agent.ini_pos = [observation['player']['pos'][0], observation['player']['pos'][2]]
            is_Macguffin = False
            agent.UPDATE(obs=observation)
            ###################################

            while agent.key_num < 3:
                if is_Macguffin:
                    agent.WALK_TO(agent.mac_pos)
                    has_Macguffin = True
                    observation = agent.MC('SENSE_ALL')
                    agent.UPDATE(obs=observation)

                agent.GET_KEY_NO_DOG()

            attempts = 0
            while not agent.check_goal_achieved:
                observation = agent.MC('SENSE_ALL')
                is_Macguffin = False
                agent.UPDATE(obs=observation)

                agent.GET_DES()

                if agent.bot_pos[0] == observation['destinationPos'][0] and agent.bot_pos[1] == \
                        observation['destinationPos'][2]:
                    agent.MC('MOVE x')
                    agent.MC('PLACE polycraft:macguffin')
                else:
                    agent.GET_MAC()
                    agent.GET_DES()

                attempts += 1
                # if it's taking too long, try a reset.
                if attempts >= 10:
                    # too many attempts. refresh memory
                    temp = agent.ini_pos
                    agent.RESET()
                    agent.ini_pos = temp
                    attempts = 0

            while agent.check_goal_achieved and not agent.check_gameOver:
                time.sleep(.5)
                agent.MC('CHECK_COST')
                observation = agent.MC('SENSE_ALL')
                agent.UPDATE(obs=observation)

            time.sleep(.5)
            agent.MC('CHECK_COST')
            time.sleep(.5)
            agent.MC('CHECK_COST')
            time.sleep(.5)
            agent.MC('CHECK_COST')

            game = game + 1

        except Exception as e:
            agent.MC("REPORT_NOVELTY -m 'Novelty Detected. Wish I was a TA2 Agent'")
            print("Novelty Found!")
            time.sleep(1)
            agent.MC("GIVE_UP")
            agent.RESET()
            print("Exception Occurred: I Give Up!\n" + str(e))
            traceback.print_exc()
            # time.sleep(30)
            game = game + 1
