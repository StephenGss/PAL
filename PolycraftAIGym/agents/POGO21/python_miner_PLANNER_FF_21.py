


# coordenates confusion
# Maps and humans use [x,z]
# matrixes use [z,x]



def CLEARALL():
      "CLEARALL says it self explainnatory"
      all = [var for var in globals() if "__" not in (var[:2], var[-2:])]
      for var in all:
            del globals()[var]

CLEARALL()



# packages
from typing import OrderedDict
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

import astar


game_low_level_actions = 0


# set a random seed
#random.seed(29)

# check and define the working directory
os.getcwd()
# os.chdir('C:/Users/dolivenca3/OneDrive/2_2019_America/2019/POLYCRAFT/5_RL_python')
# os.chdir('C:/Users/dolivenca/OneDrive/2_2019_America/2019/POLYCRAFT/5_RL_python')
os.chdir('/home/dolivenca/Desktop/VScode')

container_codes = {
                  -1:'action bar',  
                  -2:'left hand',
                  -3:'personal inventory',
                  50:'chest'
                  }

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
      
      '':-1
      }

recipes = {
      5:[17,0,0,0,0,0,0,0,0],                         # craft planks from log
      280:[5,0,0,5,0,0,0,0,0],                        # craft sticks from planks
      6321:[5,280,5,5,0,5,0,5,0],                     # craft tree tap
      5989:[280,280,280,5,280,5,0,5399,0],            # craft wooden pogo stick
      57:[264,264,264,264,264,264],                   # craft diamond block
      58:[5,5,0,5,5,0,0,0,0],                         # craft crafting table
      271:[5,5,0,5,280,0,0,280,0],                    # craft wood axe
      54:[5,5,5,5,0,5,5,5,5]                          # craft chest
      }
      
recipes_output = {
      5:4,
      280:4, 
      6321:1,
      5989:1,
      57:1,
      58:1,
      271:1,
      54:1      
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
      13:['USE(obj = 5403)'],

      15:['CRAFT(5989)']                                          # craft diamond Ti pogo stick
      }

observation = '{"BlockInFront":{"id":0},"inventory":{},"Player":{"pos":[27,2,27],"facing":"WEST"},"DestinationPos":[0,0,0],"map":{"blocks":[35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,17,0,0,0,0,35,0,35,0,0,17,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,17,0,17,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,17,0,0,17,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,35,0,35,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,35,0,35,0,0,0,17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,35,0,35,0,0,0,0,17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"size":[34,34,34]}}\r\n'

bot_pos=[0,0]



def VIEW_MATRIX(m):
      "to visualize a matrix in all its glory"
      import sys
      import numpy
      numpy.set_printoptions(threshold=sys.maxsize)
      print(m)

# VIEW_MATRIX(map)



map = numpy.repeat(-1,150*150)
map = map.reshape(150,150)

big_map_to_show = numpy.repeat(-1,150*150)
big_map_to_show = big_map_to_show.reshape(150,150)

# set plot size and will stay this size
plt.rcParams['figure.figsize']=(3,3)

def UPDATE(obs):
      
      global map
      global map_side
      global bot_pos
      global inv
      global invent
      global facing
      global traders
      global doors
      global map_small
      
      bot_pos = [ obs['player']['pos'][0],obs['player']['pos'][2] ]         # matrix coordenates
      
      facing = obs['player']['facing']
     
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
        if map_list[i]=='minecraft:bedrock': 
          map_list[i]=7
          map_to_show[i]=7
        if map_list[i]=='minecraft:air': 
          map_list[i]=0
          map_to_show[i]=0
        if map_list[i]=='minecraft:dirt': 
          map_list[i]=3
          map_to_show[i]=3    
        if map_list[i]=='minecraft:log': 
          map_list[i]=17
          map_to_show[i]=5
        if map_list[i]=='minecraft:crafting_table': 
          map_list[i]=58
          map_to_show[i]=6
        if map_list[i]=='polycraft:tree_tap': 
          map_list[i]=6321
          map_to_show[i]=6
        if map_list[i]=='minecraft:diamond_ore':        
          map_list[i]=56
          map_to_show[i]=6
        if map_list[i]=='polycraft:block_of_platinum':        
          map_list[i]=5401
          map_to_show[i]=6
        if map_list[i]=='polycraft:plastic_chest':        
          map_list[i]=5403
          map_to_show[i]=6
        if map_list[i]=='minecraft:wooden_door':        
          map_list[i]=64
          map_to_show[i]=8
        if map_list[i]=='polycraft:safe':        
          map_list[i]=5001
          map_to_show[i]=6         

      map_small = numpy.copy(map_list)
      map_small = map_small.reshape((map_side_x,map_side_y))

      map_to_show = map_to_show.astype(numpy.float)
      map_to_show = map_to_show.reshape((map_side_x,map_side_y))

      for i in range(map_small.shape[0]):
            for j in range(map_small.shape[1]):
                  map[obs['map']['origin'][0] + i,obs['map']['origin'][2] + j] = map_small[i,j]
                  big_map_to_show[obs['map']['origin'][0] + i,obs['map']['origin'][2] + j] = map_to_show[i,j]

      traders = {}
      for i in obs['entities']:
            # print(obs['entities'][i])
            # print(obs['entities'][i]['pos'][0],"  ",obs['entities'][i]['pos'][2])
            # print('')
            # create dic of traders
            if obs['entities'][i]['type']=='EntityTrader':
                  traders.update({60000+int(i):{'pos':[obs['entities'][i]['pos'][0],obs['entities'][i]['pos'][2]],'trades':{},'dist':( ( obs['entities'][i]['pos'][0]-bot_pos[0])**2 + (obs['entities'][i]['pos'][2]-bot_pos[1])**2 )**(1/2) }})
                  map[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 60000 + obs['entities'][i]['id']
                  big_map_to_show[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 10
            else:
                  if obs['entities'][i]['type']=='EntityPogoist':
                        map[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 61000 + obs['entities'][i]['id']
                        big_map_to_show[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 11
                  else:
                        map[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 60000 + obj_codes[obs['entities'][i]['item']]
                        #print(map[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])])
                        big_map_to_show[int(obs['entities'][i]['pos'][0]),int(obs['entities'][i]['pos'][2])] = 9
      
      doors = {}
      for i in numpy.transpose(numpy.where(map==64)):
            print(i)
            doors[ ((i[0]-bot_pos[0])**2 + (i[1]-bot_pos[1])**2 )**(1/2) ] = i

      # Map plot
      # plt.close() # close plot 
      ## big_map_to_show[bot_pos[0],bot_pos[1]] = 13
      # plt.figure(figsize=(3,3)) # set plot size one time     
      ## plt.imshow(numpy.transpose(big_map_to_show)) #, cmap="gray")
 
      ## plt.show(block=False)
      ## plt.pause(0.0001)

# observation = MC('SENSE_ALL')
# UPDATE(obs = observation)



### function to sample by wiegths
def weighted_choice(objects, weights):
      """ returns randomly an element from the sequence of 'objects', 
        the likelihood of the objects is weighted according 
        to the sequence of 'weights', i.e. percentages."""
      
      weights = numpy.array(weights, dtype=numpy.float64)
      sum_of_weights = weights.sum()
      # standardization:
      numpy.multiply(weights, 1 / sum_of_weights, weights)
      weights = weights.cumsum()
      x = numpy.random.uniform(low=0.0, high=1.0, size=1)
      for i in range(len(weights)):
            if x < weights[i]:
                  return objects[i]

# weighted_choice(objects = [1,2,3,4,5,6], weights = [1,2,3,4,5,10])



########################################## Astar ###########################################################

# map for Astar
def map_to_string(map1):
      map_side1=int(len(map1)) 
      map_for_Astar = str()
      for i in range(map1.shape[0]):
            for ii in range(map1.shape[1]):
                  if map1[ii,i] == 0 or map1[ii,i] == 64:
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
      global game_low_level_actions
      
      W_bot_pos = bot_pos.copy()                                                                       # map coordenates [x,z]
      if (map[new_pos[0],new_pos[1]] == -1 or map[new_pos[0],new_pos[1]] == 7):       # verify if the new position is not within the map
            print('Destination out of the world')
      else:
            if ( map[new_pos[0],new_pos[1]]!=0 ):                                               # if destination in occupied
                  free_places = numpy.array(numpy.where(map==0))                                # matrix coordenates [z,x] | find free places  
                  free_places = numpy.vstack((free_places,[0] * free_places.shape[1]))          
                  free_places.shape
                  for i in range(free_places.shape[1]):
                        free_places[2,i] = ( (free_places[0,i] - new_pos[0])**2 + (free_places[1,i] - new_pos[1])**2 )**(1/2)       # distance of new_pos to free places
                  
                  free_places_close = numpy.where(free_places[2,:] == numpy.min(free_places[2,:] ))[0]      # choose the closest free place
                  ##len(free_places_close)
                  
                  if ( len(free_places_close) == 1 ):                                                       # if closest free place is just one
                        new_pos = free_places[0:2,free_places_close].transpose().tolist()[0]                # matrix coordenates [z,x] | choose it as the new new_pos
                  else:                                                                                     # if not, choose the one closest to the bot 
                        free_places_close = free_places[0:2,free_places_close].transpose().tolist()         # matrix coordenates [z,x]
                        free_places_dist_to_bot = [0] * len(free_places_close)
                        for ii in range(len(free_places_close)):
                              free_places_dist_to_bot[ii] = ( (free_places_close[ii][0] - bot_pos[0])**2 + (free_places_close[ii][1] - bot_pos[1])**2 )**(1/2)
                        
                        new_pos = free_places_close[numpy.where(free_places_dist_to_bot == numpy.min(free_places_dist_to_bot))[0][0]]      # matrix coordenates [z,x]
                        new_pos = [new_pos[0],new_pos[1]]                                                   # map coordenates
            
            if (bot_pos == new_pos):                                                                        # if the new_pos is equal to the bot_pos, the bot is there already
                  print('Already there')
            else:
                  # Astar #
                  start = tuple(bot_pos)                                            # we choose to start at the upper left corner
                  goal = tuple(new_pos)                                             # we want to reach the lower right corner
                  map_for_Astar = map_to_string(map)
                  foundPath = list(MazeSolver(map_for_Astar).astar(start, goal))    # let's solve it
                  # print(drawmaze(map_for_Astar, list(foundPath)))                   # print the solution to verify
                  

                  for i in range(len(foundPath)-1):
                        move = numpy.subtract( foundPath[i+1], foundPath[i] )
                        if ( sum(move == [1,0]) == 2 ): 
                              MC('MOVE_EAST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)  
                        if ( sum(move == [1,1]) == 2 ): 
                              MC('LOOK_SOUTH')
                              MC('SMOOTH_MOVE Q')
                              #MC('MOVE_SOUTH_EAST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)
                        if ( sum(move == [0,1]) == 2 ): 
                              observation = MC('MOVE_SOUTH')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)
                        if ( sum(move == [-1,1]) == 2 ): 
                              MC('LOOK_SOUTH')
                              MC('SMOOTH_MOVE E') 
                              #observation = MC('MOVE_SOUTH_WEST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)
                        if ( sum(move == [-1,0]) == 2 ): 
                              observation = MC('MOVE_WEST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)
                        if ( sum(move == [-1,-1]) == 2 ): 
                              MC('LOOK_NORTH')
                              MC('SMOOTH_MOVE Q')
                              #observation = MC('MOVE_NORTH_WEST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)
                        if ( sum(move == [0,-1]) == 2 ):
                              observation = MC('MOVE_NORTH')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)
                        if ( sum(move == [1,-1]) == 2 ): 
                              MC('LOOK_NORTH')
                              MC('SMOOTH_MOVE E')
                              #observation = MC('MOVE_NORTH_EAST')
                              observation = MC('SENSE_ALL')
                              UPDATE(observation)
                              game_low_level_actions += 1
                              #time.sleep(1)

# WALK_TO([50,40])



def FIND_NEAREST(object):
      "Find nearest object in the map relative to the bot"
      Objects = numpy.where(map==object)                     # find the objects in the map
      if (len(Objects[0])==0):
            print('NO such object present on map.')
            return(19760429)
      else:
            Objects_dist_to_bot = [0] * len(Objects[0])      # create a column to store the Euclidian distances
            for i in range(len(Objects[0])):                 
                  # calculate the Euclidian distances of the objects to the player
                  Objects_dist_to_bot[i] = ( (Objects[0][i] - bot_pos[0])**2 + (Objects[1][i] - bot_pos[1])**2 )**(1/2)
            
            # find the object that is at the minimum distance
            aux = numpy.where( Objects_dist_to_bot == numpy.min(Objects_dist_to_bot))[0][0]
            Object = [Objects[0][aux],Objects[1][aux]]
            return(Object)

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


facing = 'WEST'
def LOOK_(cardinal = facing):
      if cardinal=='NORTH': obs = MC('LOOK_NORTH')
      if cardinal=='EAST': obs = MC('LOOK_EAST')
      if cardinal=='SOUTH': obs = MC('LOOK_SOUTH')
      if cardinal=='WEST': obs = MC('LOOK_WEST')
      return(obs)

# observation = LOOK_('NORTH'); observation=MC("SENSE_ALL") ;UPDATE(observation)



def COLLECT_FROM_BLOCK(container_pos=19760429):
      "Function to collect objects from containers"
      
      global inv
      global invent
      global bot_pos
      global game_low_level_actions
      
      if (container_pos==19760429):
            print("No container position specified")
      else:
            if ( map[ container_pos[0],container_pos[1] ] != 54 and map[ container_pos[0],container_pos[1] ] != 6321 ):
                  print("No container at positon ",container_pos)
            else:
                  good_pos = FIND_PLACE_NEARBY(container_pos)
                  WALK_TO(good_pos)
                  TURN_TO( obj_pos = container_pos )
                  MC('EXTRACT_RUBBER')
                  game_low_level_actions += 1
                  observation = MC("SENSE_ALL")
                  UPDATE(observation)

# COLLECT_FROM_BLOCK(container_pos=FIND_NEAREST(object=6321))



def RECIPES_SCAN(x):
      "Function to get the recipes"
      
      global recipes
      global recipes_output
      
      recipes = {}
      recipes_output = {}
      for i in x['recipes']:
          recipes[obj_codes[i['outputs'][0]['Item']]] = [0,0,0,0,0,0,0,0,0]
          recipes_output[obj_codes[i['outputs'][0]['Item']]] = i['outputs'][0]['stackSize']
          for ii in i['inputs']:
              recipes[obj_codes[i['outputs'][0]['Item']]][max(0,ii['slot'])] = obj_codes[ii['Item']]

# RECIPES_SCAN(x = MC('SENSE_RECIPES'))



def GET_BLOCK(object):
      "get natural resurce function - only for objects that cannot be crafted, they must be harvested by breaking block"
      UPDATE(obs = MC('SENSE_ALL'))
      break_outcome = 264 if object==56 else object
      break_outcome_number = 9 if object==56 else 1
      inv_before = inv[str(break_outcome)] if (str(break_outcome) in inv) else 0
      obj_pos = FIND_NEAREST(object)
      if obj_pos != 19760429:
            if object == 56 or object == 5401:
                  MC('select_item minecraft:iron_pickaxe')     
            good_pos = FIND_PLACE_NEARBY(obj_pos)
            WALK_TO(good_pos)
            if (bot_pos == list(good_pos)):
                  TURN_TO(obj_pos = obj_pos)
            UPDATE(obs = MC("SENSE_ALL"))
            if obj_pos == FIND_NEAREST(object):
                  MC('BREAK_BLOCK')
                  time.sleep(2)
                  UPDATE(obs = MC('SENSE_ALL'))
                  inv_after = inv[str(break_outcome)] if (str(break_outcome) in inv) else 0
                  if inv_after != inv_before + break_outcome_number:
                        #UPDATE(obs = MC('SENSE_ALL'))
                        if (break_outcome+60000) in map:
                              WALK_TO(FIND_NEAREST(break_outcome+60000))
                        else:
                              GET_BLOCK(object)
                  UPDATE(obs = MC('SENSE_ALL'))
            else:
                  if object == 56 and not(56 in map):
                        USE(obj = 5403)
                        PLUNDER_SAFE()
                  else:
                        GET_BLOCK(object)

# GET_BLOCK(object=50)
# GET_BLOCK(object=17)
# GET_BLOCK(object=5401)
# GET_BLOCK(object=56)



def CHECK_RECIPES_INGREDIANTS(object):
      "function to see what is needed to craft the object"
      
      global action_failed
      global available_materials 
            
      if  not (object in recipes):                                                        # check to see if there is a recipe for the object
            print('No available recipe.')
            action_failed = True
      else:
            recipes[object]                                                               # rertrive the recipe for the object
            needs={}                                                                      # create dictionary needs
            recip={}
            for i in recipes[object]: recip[i]=recipes[object].count(i)                   # get the needs from the recipe
            if 0 in recip: recip.pop(0)
            global available_materials                                                    # take out the zeros
            for ii in recip:                                                              # cycling the needs
                  if not (str(ii) in invent):                                                     # if the material in need is not in the inventory 
                        print('You do not have the required materials')
                        available_materials = False
                        needs[ii] = recip[ii]
                  else:                                                                   # if the material in need is in the inventory check to see is the amount is enough 
                        available_materials = True
                        if recip[ii] - invent[str(ii)] > 0: needs[ii] = recip[ii] - invent[str(ii)]
         
      return(needs)

# CHECK_RECIPES_INGREDIANTS(57)
# CHECK_RECIPES_INGREDIANTS(54)
# invent[5]=1
# invent[17]=2
# invent[280]=1
# CHECK_RECIPES_INGREDIANTS(5988)
# CHECK_RECIPES_INGREDIANTS(271)
# CHECK_RECIPES_INGREDIANTS(5)



def PLACE_BLOCK(object, place_pos):
      
      global map
      global inv
      global invent
      global bot_pos
      global game_low_level_actions
      
      if not str(object) in invent:                                        # verify object availability
            print('No object in inventory')
      else:
            if place_pos == 19760429:
              print ('No tree on map.')
              return
            else:
              if place_pos[0] < 1 and place_pos[0] > 100 and place_pos[1] < 1 and place_pos[1] > 100:
                  print('Destination out of the world')
              else:
                  if object == 58: 
                        # verify is place_pos is already ocuppied
                        if (map[place_pos[0],place_pos[1]]!=0):
                              print('Possition occupied')
                        else:
                              good_pos = FIND_PLACE_NEARBY(place_pos)
                              WALK_TO( good_pos ) 
                              TURN_TO( obj_pos = place_pos ) 
                              MC('PLACE_CRAFTING_TABLE')     # place crafting table
                              game_low_level_actions += 1
                  if object == 6321: 
                        if (map[place_pos[0],place_pos[1]]!=17):
                              print('No tree present')
                        else:
                              tap_pos = FIND_PLACE_NEARBY(place_pos)
                              good_pos = FIND_PLACE_NEARBY(tap_pos)
                              WALK_TO( good_pos )
                              TURN_TO( obj_pos = tap_pos )
                              MC('PLACE_TREE_TAP')         # place tree tap
                              game_low_level_actions += 1
                  observation = MC("SENSE_ALL")                      # increment game counter
                  UPDATE(observation)                             # update the RL 

# PLACE_BLOCK(object=58, place_pos=[2,5])
# PLACE_BLOCK(object=6321, place_pos=FIND_NEAREST(17))



def CRAFT(object):                                                                        # check to see if there is a recipe for the object
      "CRAFT function"
      
      global action_failed                                                                # create a global variable to store if the action was sucessful or not 
      global bot_pos
      global inv
      global invent
      global game_low_level_actions
      
      observation = MC("SENSE_ALL")
      UPDATE(observation)                                                                        # update BOT position and inventory
      if  not (object in recipes.keys()):                                                 # if the object is not craftable
            print('No available recipe.')
            action_failed = True                                                          # action will fail
      else:
            # verify availability of components
            needs = CHECK_RECIPES_INGREDIANTS(object)                                     # if the object is craftable, check needs
            sum_of_needs = 0
            for i in needs:
                  sum_of_needs = sum_of_needs + needs[i]                                  # see if there are needs
            if not (sum_of_needs == 0):                                                   # if there are needs
                  print('You do not have the required materials')
                  action_failed = True                                                    # progect will fail
            else:                                                                         # if we have the necessary materials
                  if (recipes[object][2] == 0 and recipes[object][5] == 0 and sum(recipes[object][6:9]) == 0):   # if crafting that does not require crafting table
                        if object == 5: MC('CRAFT_PLANKS'); game_low_level_actions += 1                                # send command to minecraft to do planks
                        if object == 280: MC('CRAFT_STICKS');game_low_level_actions += 1                              # send command to minecraft to do sticks
                        if object == 58: MC('CRAFT_CRAFTING_TABLE');game_low_level_actions += 1                       # send command to minecraft to do crafting table
                        action_failed = False                                             # action will succed
                        obs = MC("SENSE_ALL")
                        UPDATE(obs)                                                      # update BOT position and inventory
                  else:                                                                   # if we need a crafting table
                        if not(58 in map):                                               # and there are no crafting tables in the map
                              if 17 in map:
                                    GET_BLOCK(object=17)
                                    MC('CRAFT_CRAFTING_TABLE')
                              else:
                                    if not('6' in inv):
                                          if 6+60000 in map:
                                                WALK_TO(FIND_NEAREST(6+60000))
                                                TURN_TO(FIND_PLACE_NEARBY(bot_pos))
                                                MC('PLACE minecraft:sapling')
                                                GET_BLOCK(object=17)
                                                MC('CRAFT_CRAFTING_TABLE')                                                
                                          else:
                                                print('No crafting table available.')                       # action will fail
                                                action_failed = True                                        # action will fail
                                    else:
                                          TURN_TO(FIND_PLACE_NEARBY(bot_pos))
                                          MC('PLACE minecraft:sapling')
                                          GET_BLOCK(object=17)
                                          MC('CRAFT_CRAFTING_TABLE') 
                        else:                                                             # if there is a crafting table in the map
                              WALK_TO( new_pos = FIND_NEAREST(58) )                       # go to the closest crafting table 
                              if object == 271: MC('CRAFT_AXE'); game_low_level_actions += 1                           # send command to minecraft to do axe
                              if object == 54: MC('CRAFT_CHEST'); game_low_level_actions += 1                          # send command to minecraft to do chest
                              if object == 6321: MC('CRAFT_TREE_TAP');game_low_level_actions += 1                     # send command to minecraft to do tree tap
                              if object == 57: MC('craft 1 minecraft:diamond minecraft:diamond minecraft:diamond minecraft:diamond minecraft:diamond minecraft:diamond minecraft:diamond minecraft:diamond minecraft:diamond') ; game_low_level_actions += 1 
                              if object == 5989: MC('craft 1 minecraft:stick polycraft:block_of_titanium minecraft:stick minecraft:diamond_block polycraft:block_of_titanium minecraft:diamond_block 0 polycraft:sack_polyisoprene_pellets 0') ; game_low_level_actions += 1 

                              action_failed = False                                       # action will succed
                              obs = MC("SENSE_ALL")
                              UPDATE(obs)                                                # update BOT position and inventory

# CRAFT(5)
# CRAFT(280)
# CRAFT(6321)
# CRAFT(5988)
# CRAFT(58)
# CRAFT(271)
# CRAFT(54)
# CRAFT(57)
# CRAFT(object = 5988)



# material = 'polycraft:block_of_platinum'
# quantity = 1
def TRADE(material,quantity):
      "Trade function will seek the trader with the wanted trade and do it"
      UPDATE(obs = MC('SENSE_ALL') )      # update world state  

      # check if the bot have the necessary materials for the trade
      if (str(obj_codes[material]) in inv) and (inv[str(obj_codes[material])] >= quantity):
            print('You have the necessary materials for the trade')
      else:
            print('You lack the materials for the trade')
            return()

      # finding a trader
      traders_dist = []
      for i in traders:
            traders_dist.append( traders[i]['dist'] )
      ###numpy.where(traders_dist==numpy.min(traders_dist))[0][0]
      trader = list(traders)[numpy.where(traders_dist==numpy.min(traders_dist))[0][0]]

      trade_not_found = True
      trader_list = list(traders) 
      while trade_not_found:
            WALK_TO(FIND_PLACE_NEARBY(traders[trader]['pos']))
            traders[trader]['trades'] = MC('INTERACT '+str(trader-60000))['trades']
            for i in traders[trader]['trades']['trades']:
                  print(i)
                  if i['inputs'][0]['Item'] == material and i['inputs'][0]['stackSize'] == quantity:
                        print('found')
                        trade_not_found = not( MC('TRADE '+str(trader-60000)+' '+str(material)+' '+str(quantity))['goal']['goalAchieved']   ) #['command_result']['result']
                        break
            if len(trader_list)>1:
                  trader_list.remove(trader) 
                  trader = trader_list[0]
            else:
                  break
      UPDATE(obs = MC('SENSE_ALL') )      # update world state  
      return(print('Trade concluded sucessfully.'))



def USE(obj,item='empty'):
      "use and collect MC commands"
      UPDATE(obs = MC('SENSE_ALL') )      # update world state        
      WALK_TO(FIND_PLACE_NEARBY(FIND_NEAREST(object=obj)))
      TURN_TO(obj_pos = FIND_NEAREST(object=obj))
      if item != 'empty':
            if str(item) in inv.keys():
                  MC('SELECT_ITEM '+[k for k,v in obj_codes.items() if v==item][0] )
                  MC('USE')
            else:
                  print('No item in inventory.')
      if obj == 54 or obj == 6321 or obj == 5403 or obj == 5001:
            MC('COLLECT')
      else:
            if obj != 64:
                  MC('USE')
            else: 
                  observation = MC('SENSE_ALL')
                  UPDATE(obs = observation)      # update world state        
                  MC('USE') if (observation["blockInFront"]["open"] == "false") else print('')
                  map[bot_pos[0],bot_pos[0]] = 0
                  MC('MOVE W')
                  MC('MOVE W')
                  # MC('MOVE_'+str(facing))
      UPDATE(obs = MC('SENSE_ALL') )      # update world state        

# USE(obj = 64)
# USE(obj = 5001,item = 5000)
# USE(obj = 5403)



def PLUNDER_SAFE():
      safeFound = False
      for i,ii in sorted(doors.items()):
            print(i)
            print(ii)
            WALK_TO(FIND_PLACE_NEARBY(ii))
            USE(obj = 64)
            if 5001 in map: 
                  USE(obj = 5001,item = 5000)
                  safeFound = True
                  USE(obj = 64)
                  break
            else:
                  zeros_coord = numpy.where(map==0)
                  archway_candidates = []
                  for i in range(len(zeros_coord[0])):
                        zero_candidate = [ zeros_coord[0][i],zeros_coord[1][i] ]
                        if map[zero_candidate[0],zero_candidate[1]] == 0 and (map[zero_candidate[0]+1,zero_candidate[1]] == -1 or map[zero_candidate[0]-1,zero_candidate[1]] == -1 or map[zero_candidate[0],zero_candidate[1]+1] == -1 or map[zero_candidate[0],zero_candidate[1]-1] == -1) and (map[zero_candidate[0]+1,zero_candidate[1]] != -1 or map[zero_candidate[0]-1,zero_candidate[1]] != -1 or map[zero_candidate[0],zero_candidate[1]+1] != -1 or map[zero_candidate[0],zero_candidate[1]-1] != -1):
                              archway_candidates.append(zero_candidate)
                  for i in archway_candidates:
                        WALK_TO(FIND_PLACE_NEARBY(i))
                        TURN_TO(i)
                        MC('MOVE W')
                        MC('MOVE W')
                        UPDATE(obs = MC('SENSE_ALL'))
                        if 5001 in map: # sum(sum(map == 5001)) != 0:
                              USE(obj = 5001,item = 5000)
                              safeFound = True
                              USE(obj = 64)
                              break
            if safeFound == True:
                  break      
      if (sum(sum(map == 5001)) == 0):
            print("No safe found")



def GET_RUBBER():
      while not('5399' in inv):
            if not(17 in map):
                  if not('6' in inv):
                        WALK_TO(FIND_NEAREST(6+60000))
                  TURN_TO(FIND_PLACE_NEARBY(bot_pos))
                  MC('PLACE minecraft:sapling')  
            if not(6321 in map):
                  if not('6321' in inv): 
                        CRAFT(6321)
                  if (sum(sum(map == 6321)) == 0):
                        PLACE_BLOCK(object=6321, place_pos=FIND_NEAREST(17))
                        action_res = MC('COLLECT') 
                        if action_res['command_result']['result'] != 'SUCCESS':
                              GET_BLOCK(object=6321)
                  else:
                        USE(obj = 6321)                        
                        if not('5399' in inv):
                              GET_BLOCK(object=6321)
            else:
                  USE(obj = 6321)
                  if not('5399' in inv):
                        GET_BLOCK(object=6321)



######################################### Minecraft commands ################################################################

import socket
import json

# connect to socket'
HOST = '127.0.0.1'
PORT = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT)) 



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
    return data_dict
#    if not command.startswith('START'):
#        return sock.recv(10240).decode() 

##################################################################################################################################################



########################################### Planning #################################################

MC('START')                                                         # Send the "START" command to join a new world.
time.sleep(10)

# MC("LAUNCH domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00000_I0704_N0.json")         # start the pogo stick experiment and getting an update of the state of the game

# MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00000_I0704_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00000_I0020_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00001_I0403_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00002_I0242_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00003_I0397_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00004_I0699_N0.json")

MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00005_I0745_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00006_I0739_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00007_I0352_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00008_I0055_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00009_I0712_N0.json")

MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00010_I0550_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00011_I0455_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00012_I0071_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00013_I0319_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00014_I0385_N0.json")

MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00015_I0628_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00016_I0637_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00017_I0305_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00018_I0607_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00019_I0114_N0.json")

MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00020_I0692_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00021_I0194_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00022_I0033_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00023_I0198_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00024_I0418_N0.json")

MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00025_I0869_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00026_I0899_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00027_I0181_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00028_I0782_N0.json")
MC("RESET domain ../pogo_100_PN/POGO_L00_T01_S01_X0100_U9999_V0_G00029_I0304_N0.json")



# reset map update
map = numpy.repeat(-1,150*150)
map = map.reshape(150,150)

big_map_to_show = numpy.repeat(-1,150*150)
big_map_to_show = big_map_to_show.reshape(150,150)

plt.close() # close plot 

RECIPES_SCAN(x = MC('SENSE_RECIPES'))
time.sleep(3)

observation = MC('SENSE_ALL') 
UPDATE(obs = observation)

### getting the FF plan ##
# os.getcwd()   
os.chdir('/home/dolivenca/Desktop/POGO21')        # Change the Current working Directory

numTrees = sum(sum(map==17))
numPt = sum(sum(map==5401))
numDiamondOre = sum(sum(map==56))
ff_plan_string = './ff -o POGO21_domain.pddl -f POGO21_problem_'+str(numTrees)+'_'+str(numPt)+'_'+str(numDiamondOre)+'_1.pddl'

ff_plan = os.popen(ff_plan_string).read()

len(ff_plan)
temp1 = ff_plan.split('step')
len(temp1)
temp2 = temp1[1].split('\n\ntime spent:')
temp3 = temp2[0].split('\n')
temp3 = temp3[:-1]

ff_final_plan = []
for string_i in temp3:
      temp4 = string_i.split(':')[1]
      temp5 = temp4.split(' ')[1]
      ff_final_plan.append(temp5)

ff_final_plan

time.sleep(3)

for i in ff_final_plan:
      observation = MC("SENSE_ALL")                                           # ask minecraft for an update on the state of the world
      UPDATE(observation)    
      if i == 'GET_WOOD_BLOCK': a=1
      if i == 'CRAFT_WOOD_PLANKS': a=2     
      if i == 'CRAFT_STICKS': a=3
      if i == 'CRAFT_TREE_TAP': a=4
      if i == 'CRAFT_DIAMOND_BLOCK': a=5
      if i == 'CRAFT_CRAFTING_TABLE': a=6
      if i == 'GET_DIAMOND_ORE': a=7
      if i == 'GET_PT_BLOCK': a=8
      if i == 'PILLAGE_SAFE': a=9     
      if i == 'TRADE_PT_TI': a=10 
      if i == 'TRADE_WOOD_Ti': a=11 
      if i == 'TRADE_Pt_DIAMOND': a=12 
      if i == 'GET_BLUE_KEY': a=13
      if i == 'CRAFT_POGO_STICK': a=15     

      for act in actions[a]: eval(act)       # execute action
      time.sleep(.5)



