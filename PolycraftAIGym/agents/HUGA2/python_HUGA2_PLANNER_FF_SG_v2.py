

def CLEARALL():
      "CLEARALL says it self explainnatory"
      all = [var for var in globals() if "__" not in (var[:2], var[-2:])]
      for var in all:
            del globals()[var]

CLEARALL()



# packages
from collections import OrderedDict
import numpy
import pandas
import random
import os
import plotnine
import math
import matplotlib.pyplot as plt
import itertools
import time 
import json


obj_codes = {
      'minecraft:dirt':3,
      'minecraft:log':17,
      'minecraft:planks':5,
      'minecraft:stick':280,
      'minecraft:crafting_table':58,
      'minecraft:wood_axe':271,
      'minecraft:chest':54,
      'minecraft:diamond_ore':56,
      'minecraft:diamond_block':57,
      'minecraft:diamond':264,
      'minecraft:iron_pickaxe':257,
      'minecraft:wooden_door':64,
      'minecraft:sapling':6,

      'polycraft:wooden_pogo_stick':5989,
      'polycraft:tree_tap':6321,
      'polycraft:bag_polyisoprene_pellets':5398,
      'polycraft:sack_polyisoprene_pellets':5399,
      'polycraft:powder_keg_polyisoprene_pellets':5400,
      'polycraft:block_of_platinum':5401,
      'polycraft:block_of_titanium':5402,
      'polycraft:plastic_chest':5403,
      'polycraft:key':5000,
      'polycraft:safe':5001,

      'polycraft:expblock':5500,
      'polycraft:tier_chest':5501,
      'polycraft:trap':5502,
      'polycraft:macguffin':5503,
      'polycraft:locked_door':5504,

      '':-1
      }



actions = {
      1:['GET_BLOCK(object=17)'],                                 # get wood block
      2:['CRAFT(5)'],                                             # craft planks
      3:['CRAFT(280)'],                                           # craft sticks
      4:['GET_RUBBER()'],                                         # create tree tap, place it and collect rubber
      5:['CRAFT(57)'],                                            # craft diamond block
      6:['CRAFT(58)','PLACE_BLOCK(58,FIND_NEAREST(object=0))'],   # craft crafting table
      7:['GET_BLOCK(object=56)'],                                 # get diamonds from block
      8:['GET_BLOCK(object=5401)'],                               # get Pl block
      9:['PLUNDER_SAFE()'],                                       # get blue key, open safe, get diamonds
      10:['TRADE( material = "polycraft:block_of_platinum",quantity = 1 )'],    # trade Pl block for Ti block
      11:['TRADE( material = "minecraft:log",quantity = 10 )'],   # trade wood log block for Ti block
      12:['TRADE( material = "polycraft:block_of_platinum",quantity = 2 )'],    # trade 2 Ti blocks for 9 diamonds

      15:['CRAFT(5989)']                                          # craft diamond Ti pogo stick
      }



def VIEW_MATRIX(m):
      "to visualize a matrix in all its glory"
      import sys
      import numpy
      numpy.set_printoptions(threshold=sys.maxsize)
      print(m)

# VIEW_MATRIX(map)



map = numpy.repeat(-1,150*150)
map = map.reshape(150,150)
map_side_x = 16
map_side_z = 16

big_map_to_show = numpy.repeat(-1,150*150)
big_map_to_show = big_map_to_show.reshape(150,150)

# set plot size and will stay this size
plt.rcParams['figure.figsize']=(3,3)

def UPDATE(obs):
      
      global map
      global map_side
      global mac_pos
      global bot_pos
      global inv
      global invent
      global facing
      global dog_pos
      global dog_tag
      global doors
      global archway_candidates
      global map_small
      global is_Macguffin
      global archway_pos
      global is_LockedDoor

      global locked_door_pos
      global is_archway


      bot_pos = [obs['player']['pos'][0],obs['player']['pos'][2]]         # matrix coordenates

      
      facing = obs['player']['facing']

      is_Dog = False
      is_LockedDoor = False
      is_Macguffin = False
      is_archway = False
      is_LockedDoor_Room = False
      #i nv = numpy.array([[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]])
      #inv.shape
      invent = {}
      for i in obs['inventory']:
            print(i)
            #inv = numpy.vstack([inv,[int(i), obs['inventory'][i],0,0,0,-1,1]])
            invent[str(obj_codes[obs['inventory'][i]['item']])]=obs['inventory'][i]['count']
      
      inv = invent.copy()
      # map_small = numpy.array(obs['map']['blocks'])
      map_list = obs['map']['blocks'].copy()
      map_to_show = numpy.copy(map_list)
      map_side_x = obs['map']['size'][0] # int((len(map_list))**(1/2))
      map_side_y = obs['map']['size'][2] # int((len(map_list))**(1/2)) 

      
      for i in range(len(map_list)):
        if map_list[i]=='polycraft:expblock':
          map_list[i]=obj_codes['polycraft:expblock']
          map_to_show[i]=7
        if map_list[i]=='minecraft:air':
          map_list[i]=0
          map_to_show[i]=0
        if map_list[i]=='polycraft:tier_chest':
          map_list[i]=obj_codes['polycraft:tier_chest']
          map_to_show[i]=6
        if map_list[i]=='minecraft:wooden_door':
          map_list[i]=obj_codes['minecraft:wooden_door']
          map_to_show[i]=8
        if map_list[i]=='polycraft:trap':
          map_list[i]=obj_codes['polycraft:trap']
          map_to_show[i]=9
        if map_list[i]=='polycraft:macguffin':
          map_list[i]=obj_codes['polycraft:macguffin']
          is_Macguffin = True
          map_to_show[i]=12
        if map_list[i]=='polycraft:locked_door':
          map_list[i]=obj_codes['polycraft:locked_door']
          map_to_show[i]=13


      map_small = numpy.copy(map_list)
      map_small = map_small.reshape((map_side_x,map_side_y))

      map_to_show = map_to_show.astype(numpy.float)
      map_to_show = map_to_show.reshape((map_side_x,map_side_y))


      for i in range(map_small.shape[0]):
            for j in range(map_small.shape[1]):
                  map[obs['map']['origin'][0] + i,obs['map']['origin'][2] + j] = map_small[i,j]
                  big_map_to_show[obs['map']['origin'][0] + i,obs['map']['origin'][2] + j] = map_to_show[i,j]
      for i in obs['entities']:
            #print(obs['entities'][i])
            if obs['entities'][i]['type']=='EntityPatrol':
                  map[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 60000 + obs['entities'][i]['id']
                  big_map_to_show[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 10
                  if obs['entities'][i]['color']=='red':

                        big_map_to_show[int(obs['entities'][i]['pos'][0])+1, int(obs['entities'][i]['pos'][2])] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0])-1, int(obs['entities'][i]['pos'][2])] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2]) + 1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2])- 1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) + 1, int(obs['entities'][i]['pos'][2])+1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) - 1, int(obs['entities'][i]['pos'][2])-1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0])-1, int(obs['entities'][i]['pos'][2]) + 1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0])+1, int(obs['entities'][i]['pos'][2]) - 1] = 10
                        """
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) + 2, int(obs['entities'][i]['pos'][2])] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) - 2, int(obs['entities'][i]['pos'][2])] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2]) + 2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]), int(obs['entities'][i]['pos'][2]) - 2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) + 2, int(obs['entities'][i]['pos'][2])+2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) - 2, int(obs['entities'][i]['pos'][2])-2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0])-2, int(obs['entities'][i]['pos'][2]) + 2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0])+2, int(obs['entities'][i]['pos'][2]) - 2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) + 2, int(obs['entities'][i]['pos'][2])+1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) + 2, int(obs['entities'][i]['pos'][2]) -1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) - 2, int(obs['entities'][i]['pos'][2])-1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) - 2, int(obs['entities'][i]['pos'][2]) +1] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0])-1, int(obs['entities'][i]['pos'][2]) + 2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) - 1, int(obs['entities'][i]['pos'][2])-2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0])+1, int(obs['entities'][i]['pos'][2]) - 2] = 10
                        big_map_to_show[int(obs['entities'][i]['pos'][0]) + 1, int(obs['entities'][i]['pos'][2]) + 2] = 10
                        """
      for i in obs['entities']:
            map_ = big_map_to_show
            if obs['entities'][i]['type']=='EntityDog':
                  is_Dog = True
                  map[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 61000 + obs['entities'][i]['id']
                  big_map_to_show[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 11
                  dog_pos = [int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])]
                  a = dog_pos
                  dog_tag = i
      if (13 in big_map_to_show):
            is_LockedDoor=True
            locked_door_pos_to_show = numpy.where(big_map_to_show == 13)
            locked_door_pos = FIND_NEAREST_LOCKED(locked_door_pos_to_show)
            #b = locked_door_pos
            #a = 0

      if is_Dog == False:
            dog_pos = [0,0]
      if (11 in big_map_to_show):
            is_Dog = True
            dog_pos = numpy.where(big_map_to_show == 11)
            a = dog_pos
            a = 0
      #map_small_ = map_small
      if is_Macguffin:
            mac_pos_to_show = numpy.where(map_to_show==12)
            mac_pos = [obs['map']['origin'][0] + mac_pos_to_show[0][0],obs['map']['origin'][2] + mac_pos_to_show[1][0]]

      doors = {}
      for i in numpy.transpose(numpy.where(map==5504)):
            print(i)
            doors[((i[0]-bot_pos[0])**2 + (i[1]-bot_pos[1])**2)**(1/2)] = i
      #map_ = map
      zeros_coord = numpy.where((big_map_to_show==0)|(big_map_to_show==11))
      archway_candidates = []
      archway_to_des_candidates = []
      for i in range(len(zeros_coord[0])):
            zero_candidate = [zeros_coord[0][i],zeros_coord[1][i]]
            if map[zero_candidate[0],zero_candidate[1]] == 0 and (map[zero_candidate[0]+1,zero_candidate[1]] == -1 or map[zero_candidate[0]-1,zero_candidate[1]] == -1 or map[zero_candidate[0],zero_candidate[1]+1] == -1 or map[zero_candidate[0],zero_candidate[1]-1] == -1): #and (map[zero_candidate[0]+1,zero_candidate[1]] != -1 or map[zero_candidate[0]-1,zero_candidate[1]] != -1 or map[zero_candidate[0],zero_candidate[1]+1] != -1 or map[zero_candidate[0],zero_candidate[1]-1] != -1):
                  archway_candidates.append(zero_candidate)
            if map[zero_candidate[0], zero_candidate[1]] == 0 and (
                    map[zero_candidate[0] + 1, zero_candidate[1]] != -1 and map[
                  zero_candidate[0] - 1, zero_candidate[1]] != -1 and map[
                          zero_candidate[0], zero_candidate[1] + 1] != -1 and map[
                          zero_candidate[0], zero_candidate[1] - 1] != -1):
                  archway_to_des_candidates.append(zero_candidate)
            if big_map_to_show[zero_candidate[0],zero_candidate[1]] == 11 and (map[zero_candidate[0]+1,zero_candidate[1]] == -1 or map[zero_candidate[0]-1,zero_candidate[1]] == -1 or map[zero_candidate[0],zero_candidate[1]+1] == -1 or map[zero_candidate[0],zero_candidate[1]-1] == -1): #and (map[zero_candidate[0]+1,zero_candidate[1]] != -1 or map[zero_candidate[0]-1,zero_candidate[1]] != -1 or map[zero_candidate[0],zero_candidate[1]+1] != -1 or map[zero_candidate[0],zero_candidate[1]-1] != -1):
                  archway_candidates.append(zero_candidate)
      ##################################3

      map_ = big_map_to_show
      c = archway_candidates
      archway_to_des_candidates = archway_to_des_candidates.extend(archway_candidates)
      #Map plot
      archway_pos = FIND_NEAREST(archway_candidates)

      d = archway_pos
      t = 0# close plot
      ## big_map_to_show[bot_pos[0],bot_pos[1]] = 13
      # plt.figure(figsize=(3,3)) # set plot size one time
      ## plt.imshow(numpy.transpose(big_map_to_show)) #, cmap="gray")

      ## plt.show(block=False)
      #plt.pause(0.0001)

# observation = MC('SENSE_ALL')
# UPDATE(obs = observation)



########################################## Astar ###########################################################

# map for Astar
def map_to_string(map1):
      map_side1=int(len(map1))
      map_for_Astar = str()
      for i in range(map1.shape[0]):
            for ii in range(map1.shape[1]):
                  if map1[ii,i] == 0 or map1[ii,i] == 64 or map1[ii, i] == 12:
                        map_for_Astar = map_for_Astar + ' '
                  else:
                        map_for_Astar = map_for_Astar + '+'
                  if ii == map_side1-1:
                        map_for_Astar = map_for_Astar + '\n'
      return(map_for_Astar)

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
            if self.lines[y - 1][x] == ' ' and self.lines[y - 1][x - 1] == ' ' and self.lines[y][x - 1] == ' ' and self.lines[y + 1][x - 1] == ' ' and self.lines[y + 1][x] == ' ' and self.lines[y + 1][x + 1] == ' ' and self.lines[y][x + 1] == ' ' and self.lines[y - 1][x + 1] == ' ':
                  return[(nx, ny) for nx, ny in[(x, y - 1),(x - 1, y - 1),(x - 1, y),(x - 1, y + 1),(x, y + 1),(x + 1, y + 1),(x + 1, y),(x + 1, y - 1)]if 0 <= nx < self.width and 0 <= ny < self.height and self.lines[ny][nx] == ' ']
            else:
                  return[(nx, ny) for nx, ny in[(x, y - 1),(x - 1, y),(x, y + 1),(x + 1, y)]if 0 <= nx < self.width and 0 <= ny < self.height and self.lines[ny][nx] == ' ']


###############################################################################################################################################



def WALK_TO( new_pos ):
      "WALK_TO function, go to new_pos, avoiding objects, stay in matrix, stop near an ocopied possition"

      global inv
      global invent
      global bot_pos
      global observation
      global has_Macguffin
      global dog_pos
      global locked_door_pos
      global ini_pos
      global temp_pos
      W_bot_pos = bot_pos.copy()               # map coordenates [x,z]

      if (map[new_pos[0],new_pos[1]] == -1 or map[new_pos[0],new_pos[1]] == 7):       # verify if the new position is not within the map
            print('Destination out of the world')

      else:
            if (map[new_pos[0],new_pos[1]]!=0 ):                                               # if destination in occupied
                  map_=big_map_to_show
                  free_places = numpy.array(numpy.where((big_map_to_show==0)|(big_map_to_show==12)))                                # matrix coordenates [z,x] | find free places
                  free_places = numpy.vstack((free_places,[0] * free_places.shape[1]))
                  free_places.shape
                  for i in range(free_places.shape[1]):
                        free_places[2,i] = ( (free_places[0,i] - new_pos[0])**2 + (free_places[1,i] - new_pos[1])**2 )**(1/2)       # distance of new_pos to free places

                  free_places_close = numpy.where(free_places[2,:] == numpy.min(free_places[2,:] ))[0]      # choose the closest free place
                  ##len(free_places_close)

                  if ( len(free_places_close) == 1 ):                                                       # if closest free place is just one
                        new_pos = free_places[0:2,free_places_close].transpose().tolist()[0]                # matrix coordenates [z,x] | choose it as the new new_pos
                  else:                                                                                     # if not, choose the one closest to the bot
                        free_places_close = free_places[0:2,free_places_close].transpose().tolist()   # matrix coordenates [z,x]
                        ##########check if the 4 nearest neighbors are occupied
                        free_places_close_new = []
                        for i in range(len(free_places_close)):
                              if (big_map_to_show[free_places_close[i][0]+1,free_places_close[i][1]]==0 or big_map_to_show[free_places_close[i][0]-1,free_places_close[i][1]]==0 or big_map_to_show[free_places_close[i][0],free_places_close[i][1]+1]==0 or big_map_to_show[free_places_close[i][0],free_places_close[i][1]-1]==0):
                                    free_places_close_new.append(free_places_close[i])

                        if big_map_to_show[new_pos[0],new_pos[1]]==13:
                              free_places_dist_to_door = [0] * len(free_places_close_new)
                              for ii in range(len(free_places_close_new)):
                                    free_places_dist_to_door[ii] = ((free_places_close_new[ii][0] - new_pos[0]) ** 2 + (
                                                  free_places_close_new[ii][1] - new_pos[1]) ** 2)

                              new_pos = free_places_close_new[numpy.where(free_places_dist_to_door == numpy.min(free_places_dist_to_door))[0][0]]  # matrix coordenates [z,x]
                              new_pos = [new_pos[0], new_pos[1]]
                        elif is_archway==True:
                              free_places_dist_to_door = [0] * len(free_places_close_new)
                              for ii in range(len(free_places_close_new)):
                                    free_places_dist_to_door[ii] = ((free_places_close_new[ii][0] - new_pos[0]) ** 2 + (
                                                  free_places_close_new[ii][1] - new_pos[1]) ** 2)

                              new_pos = free_places_close_new[numpy.where(free_places_dist_to_door == numpy.min(free_places_dist_to_door))[0][0]]  # matrix coordenates [z,x]
                              new_pos = [new_pos[0], new_pos[1]]
                        else:
                              free_places_dist_to_bot = [0] * len(free_places_close_new)
                              for ii in range(len(free_places_close_new)):
                                    free_places_dist_to_bot[ii] = ((free_places_close_new[ii][0] - bot_pos[0])**2 + (free_places_close_new[ii][1] - bot_pos[1])**2 )**(1/2)

                              new_pos = free_places_close_new[numpy.where(free_places_dist_to_bot == numpy.min(free_places_dist_to_bot))[0][0]]      # matrix coordenates [z,x]
                              new_pos = [new_pos[0],new_pos[1]]                                                   # map coordenates

            if (bot_pos == new_pos):                                                                        # if the new_pos is equal to the bot_pos, the bot is there already
                  print('Already there')
            else:
                  while (bot_pos != new_pos):
                        # Astar #
                        start = tuple(bot_pos)                                            # we choose to start at the upper left corner
                        goal = tuple(new_pos)                                             # we want to reach the lower right corner
                        map_for_Astar = map_to_string(big_map_to_show)
                        test = MazeSolver(map_for_Astar).astar(start, goal)
                        if test==None:
                              MC('NOP')
                              observation = MC('SENSE_ALL')
                              UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)
                              if abs(bot_pos[0] - new_pos[0]) > map_side_x or abs(bot_pos[1] - new_pos[1]) > map_side_z:
                                    WALK_TO_NEXT_ROOM()

                              continue

                        foundPath = list(test)# let's solve it

                        # print(drawmaze(map_for_Astar, list(foundPath)))                   # print the solution to verify
                        if len(foundPath)==1 or len(foundPath)==0:
                              MC('USE')
                              observation = MC('SENSE_ALL')
                              UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              continue

                        i=0
                        move = numpy.subtract(foundPath[i+1], foundPath[i])
                        if ( sum(move == [1,0]) == 2 ):
                              MC('MOVE_EAST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              a = ini_pos
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                        if ( sum(move == [1,1]) == 2 ):
                              MC('LOOK_SOUTH')
                              MC('SMOOTH_MOVE Q')
                              #MC('MOVE_SOUTH_EAST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                        if ( sum(move == [0,1]) == 2 ):
                              observation = MC('MOVE_SOUTH')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                        if ( sum(move == [-1,1]) == 2 ):
                              MC('LOOK_SOUTH')
                              MC('SMOOTH_MOVE E')
                              #observation = MC('MOVE_SOUTH_WEST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                        if ( sum(move == [-1,0]) == 2 ):
                              observation = MC('MOVE_WEST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                        if ( sum(move == [-1,-1]) == 2 ):
                              MC('LOOK_NORTH')
                              MC('SMOOTH_MOVE Q')
                              #observation = MC('MOVE_NORTH_WEST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                        if ( sum(move == [0,-1]) == 2 ):
                              observation = MC('MOVE_NORTH')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                        if ( sum(move == [1,-1]) == 2 ):
                              MC('LOOK_NORTH')
                              MC('SMOOTH_MOVE E')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              if is_Macguffin:
                                    WALK_TO(mac_pos)
                                    has_Macguffin = True
                                    observation = MC('SENSE_ALL')
                                    UPDATE(obs=observation)
                              if bot_pos==ini_pos:
                                    WALK_TO(temp_pos)

                              #time.sleep(1)
                  #if bot_pos==ini_pos:
                   #     WALK_TO(W_bot_pos)

# WALK_TO(new_pos = [62,49])



def FIND_NEAREST(object):
      "Find nearest object in the map relative to the bot"
      #Objects = numpy.where(map==object)                     # find the objects in the map
      Objects = object
      if (len(Objects)==0):
            print('NO such object present on map.')
            return(19760429)
      else:
            Objects_dist_to_bot = [0] * len(Objects)      # create a column to store the Euclidian distances
            for i in range(len(Objects)):
                  # calculate the Euclidian distances of the objects to the player
                  Objects_dist_to_bot[i] = ( (Objects[i][0] - bot_pos[0])**2 + (Objects[i][1] - bot_pos[1])**2 )**(1/2)

            # find the object that is at the minimum distance
            aux = numpy.where( Objects_dist_to_bot == numpy.min(Objects_dist_to_bot))[0][0]
            Object = [Objects[aux][0],Objects[aux][1]]
            return(Object)


def FIND_NEAREST_LOCKED(object):
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
                  Objects_dist_to_bot[i] = ((Objects[0][i] - bot_pos[0]) ** 2 + (Objects[1][i] - bot_pos[1]) ** 2) ** (
                                1 / 2)

            # find the object that is at the minimum distance
            aux = numpy.where(Objects_dist_to_bot == numpy.min(Objects_dist_to_bot))[0][0]
            Object = [Objects[0][aux], Objects[1][aux]]
            return (Object)
# FIND_NEAREST(object=17)
# object = object +60000



def FIND_PLACE_NEARBY(pos):
      "Find a place in one of the four cardinal squares near a position"
      cardinal_pos = [(pos[0]+1,pos[1]),(pos[0],pos[1]+1),(pos[0]-1,pos[1]),(pos[0],pos[1]-1)]
      cardinal_dist_bot = []
      to_remove = []
      for i in cardinal_pos:
            if map[i]==0:
                  cardinal_dist_bot.append( ( (i[0] - bot_pos[0])**2 + (i[1] - bot_pos[1])**2 )**(1/2) )
            else:
                  to_remove.append(i)
      for ii in to_remove:
            cardinal_pos.remove(ii)
      return( cardinal_pos[ numpy.where( cardinal_dist_bot == numpy.min(cardinal_dist_bot) )[0][0] ] )

# FIND_PLACE_NEARBY([50,40])



def TURN_TO(obj_pos):
      global obs
      UPDATE(obs = MC('SENSE_ALL'))
      if obj_pos[0] - bot_pos[0] == 1 and obj_pos[1] - bot_pos[1] == 0:
            obs = MC('LOOK_EAST')
            facing = 'EAST'

      if obj_pos[0] - bot_pos[0] == -1 and obj_pos[1] - bot_pos[1] == 0:
            obs = MC('LOOK_WEST')
            facing = 'WEST'

      if obj_pos[0] - bot_pos[0] == 0 and obj_pos[1] - bot_pos[1] == -1:
            obs = MC('LOOK_NORTH')
            facing = 'NORTH'

      if obj_pos[0] - bot_pos[0] == 0 and obj_pos[1] - bot_pos[1] == 1:
            obs = MC('LOOK_SOUTH')
            facing = 'SOUTH'

      return(obs)

# TURN_TO(obj_pos = [50,40])      # LOOK_east

def WALK_TO_NEXT_ROOM():
      global temp_pos
      global bot_pos
      temp_pos = bot_pos
      "Walk to the dog, interacts with it, follows it and retrive the key from the safe."
      is_archway = True
      #if dog_pos == [0,0]:
      #dog_pos = archway_pos
      WALK_TO(archway_pos)

      #TURN_TO(archway_pos)

def WALK_TO_LOCKED_DOOR():
      global temp_pos
      global bot_pos
      temp_pos = bot_pos
      "Walk to the dog, interacts with it, follows it and retrive the key from the safe."
      #if dog_pos == [0,0]:
      #dog_pos = archway_pos
      WALK_TO(locked_door_pos)
      TURN_TO(locked_door_pos)

def UNLOCK_DOOR():
      o = observation

      for a in observation['inventory']:
            if observation['inventory'][a]['item'] == 'polycraft:key':
                  MC('SELECT_ITEM polycraft:key'+ ' '+ str(observation['inventory'][a]['damage']))
                  #MC('SELECT_ITEM polycraft:macguffin')
                  #observation['inventory']['selectedItem']['damage'] = observation['inventory'][a]['damage']
                  #observation['inventory']['selectedItem']['slot'] = a
                  result = MC('USE')
                  if result['command_result']['result'] == 'SUCCESS':
                        break

      MC('move w')
      #MC('move w')




def WALK_TO_DES():
      global temp_pos
      global bot_pos
      temp_pos = bot_pos
      WALK_TO([observation['destinationPos'][0],observation['destinationPos'][2]])

      #MC('PLACE_MACGUFFIN')







def GET_KEY():
      global key_num
      global has_Macguffin
      global mac_pos
      global dog_pos
      global temp_pos
      global bot_pos

      "Walk to the dog, interacts with it, follows it and retrive the key from the safe."
      #if dog_pos == [0,0]:
      #dog_pos = archway_pos
      while dog_pos == [0, 0]:

            WALK_TO_NEXT_ROOM()
            MC('move w')
            #MC('move w')
            UPDATE(obs=MC('SENSE_ALL'))

      temp_pos = bot_pos
      WALK_TO(dog_pos)
      MC("interact " + dog_tag)

      dog_pos_list = [[1,1],[2,2],dog_pos]
      bot_pos_tminus1 = bot_pos
      nop_count = 0
      while (dog_pos_list[2] != dog_pos_list[1] or dog_pos_list[1] != dog_pos_list[0]) or not(map[dog_pos[0]-1,dog_pos[1]] == 5501 or map[dog_pos[0],dog_pos[1]-1] == 5501 or map[dog_pos[0]+1,dog_pos[1]] == 5501 or map[dog_pos[0],dog_pos[1]+1] == 5501):
            temp_pos = bot_pos
            WALK_TO(new_pos = dog_pos)
            UPDATE(obs = MC('SENSE_ALL'))
            """
            if is_Macguffin:
                  WALK_TO(mac_pos)
                  has_Macguffin = True
                  observation = MC('SENSE_ALL')
                  UPDATE(obs=observation)
            """
            if bot_pos == bot_pos_tminus1:
                 MC("USE")
                 nop_count += 1
                 if nop_count > 10:
                       MC("Move w")

            UPDATE(obs = MC('SENSE_ALL'))
            if bot_pos == ini_pos:
                  WALK_TO(temp_pos)

            while dog_pos == [0, 0]:
                  observation = MC('SENSE_ALL')
                  UPDATE(obs=observation)
                  WALK_TO_NEXT_ROOM()
                  MC('move w')
                  observation = MC('SENSE_ALL')
                  UPDATE(obs=observation)
                  #MC('move w')
                  """
                  if is_Macguffin:
                        WALK_TO(mac_pos)
                        has_Macguffin = True
                        observation = MC('SENSE_ALL')
                        UPDATE(obs=observation)
                   """
            bot_pos_tminus1 = bot_pos
            dog_pos_list.append(dog_pos)
            dog_pos_list = dog_pos_list[1:4]

      safe_location = []
      if ( map[dog_pos[0]-1,dog_pos[1]] == 5501 ):
            safe_location.append([dog_pos[0]-1,dog_pos[1]])
      if ( map[dog_pos[0],dog_pos[1]-1] == 5501 ):
            safe_location.append([dog_pos[0],dog_pos[1]-1])
      if ( map[dog_pos[0]+1,dog_pos[1]] == 5501 ):
            safe_location.append([dog_pos[0]+1,dog_pos[1]])
      if ( map[dog_pos[0],dog_pos[1]+1] == 5501 ):
            safe_location.append([dog_pos[0],dog_pos[1]+1])
      for i in safe_location:
            if not([bot_pos[0]-1,bot_pos[1]] == i or [bot_pos[0],bot_pos[1]-1] == i or [bot_pos[0]+1,bot_pos[1]] == i or [bot_pos[0],bot_pos[1]+1] == i):
                  temp_pos = bot_pos
                  WALK_TO(list(FIND_PLACE_NEARBY(pos = i)))

            TURN_TO(obj_pos = i)
            result = MC("collect")
            if result['command_result']['result'] == 'SUCCESS':
                  key_num += 1
                  break
      observation = MC('SENSE_ALL')
      UPDATE(obs=observation)

def GET_MAC():

      global has_Macguffin
      global mac_pos

      observation = MC('SENSE_ALL')
      UPDATE(obs=observation)

      if not has_Macguffin:

            while not is_Macguffin:
                  #WALK_TO(mac_pos)
                  #has_Macguffin = True
                  WALK_TO_NEXT_ROOM()
                  MC('move w')
                  #MC('move w')
                  observation = MC('SENSE_ALL')
                  UPDATE(obs=observation)
            if is_Macguffin:
                  temp_pos = bot_pos
                  WALK_TO(mac_pos)
                  has_Macguffin = True
                  observation = MC('SENSE_ALL')
                  UPDATE(obs=observation)

def GET_DES():

      global is_LockedDoor
      global locked_door_pos
      global ini_pos
      #WALK_TO_DES()


      while not is_LockedDoor:
            # WALK_TO(mac_pos)
            # has_Macguffin = True
            #WALK_TO(locked_door_pos)
            WALK_TO_NEXT_ROOM()
            MC('move w')
            MC('move w')
            # MC('move w')
            observation = MC('SENSE_ALL')
            UPDATE(obs=observation)
      if is_LockedDoor:
            UNLOCK_DOOR()
            WALK_TO_LOCKED_DOOR()
            UNLOCK_DOOR()
            MC('move w')


      MC('move w')
      observation = MC('SENSE_ALL')
      UPDATE(obs=observation)


      WALK_TO_DES()








######################################### Minecraft commands ################################################################

import socket
import json

# connect to socket'
HOST = '127.0.0.1'
PORT = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
check_gameOver = False



def MC(command):
    "function that enable the communication with minecraft"
    print( command )
    sock.send(str.encode(command + '\n'))
    BUFF_SIZE = 4096  # 4 KiB
    data = b''
    while True:
      part = sock.recv(BUFF_SIZE)
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
            check_gameOver = True
            print("Game Over flag detected")
    return data_dict

##################################################################################################################################################



########################################### Planning #################################################


PYDEV_DEBUG=True
time.sleep(3)

global key_num
global has_Macguffin
global ini_pos

game = 1
while game < 100+1:
      try:
            key_num = 0
            has_Macguffin = False
            check_gameOver = False
            # reset map update
            map = numpy.repeat(-1,150*150)
            map = map.reshape(150,150)

            big_map_to_show = numpy.repeat(-1,150*150)
            big_map_to_show = big_map_to_show.reshape(150,150)

            #plt.close() # close plot

            observation = MC('SENSE_ALL')
            ini_pos = [observation['player']['pos'][0],observation['player']['pos'][2]]
            is_Macguffin = False
            UPDATE(obs = observation)
            ###################################

            while key_num<3:
                  observation = MC('SENSE_ALL')
                  UPDATE(obs=observation)

                  if is_Macguffin:
                      WALK_TO(mac_pos)
                      has_Macguffin = True
                      observation = MC('SENSE_ALL')
                      UPDATE(obs=observation)

                  GET_KEY()
                  observation = MC('SENSE_ALL')
                  UPDATE(obs=observation)

                  #GET_KEY()
                  #GET_KEY()
                  #GET_KEY()

            while not check_gameOver:
                  # reset map update
                  map = numpy.repeat(-1, 150 * 150)
                  map = map.reshape(150, 150)

                  big_map_to_show = numpy.repeat(-1, 150 * 150)
                  big_map_to_show = big_map_to_show.reshape(150, 150)

                  # plt.close() # close plot

                  observation = MC('SENSE_ALL')
                  is_Macguffin = False
                  UPDATE(obs=observation)

                  GET_DES()

                  if bot_pos[0] == observation['destinationPos'][0] and bot_pos[1] == observation['destinationPos'][2]:
                        MC('MOVE x')
                        MC('PLACE polycraft:macguffin')
                  else:
                        GET_MAC()
                        GET_DES()


            while check_gameOver:
                  time.sleep(.5)
                  MC('CHECK_COST')

            game = game + 1

      except Exception as e:
            MC("REPORT_NOVELTY -m 'Novelty Detected. Wish I was a TA2 Agent'")
            print("Novelty Found!")
            time.sleep(30)
            MC("GIVE_UP")
            print("Exception Occurred: I Give Up!\n" + str(e))
            time.sleep(30)
            game = game + 1







