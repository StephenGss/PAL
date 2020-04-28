import PolycraftGym, time, json, numpy as np
import neatfast as neat
import numpy as np
import cv2


def main():

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         'config-neat')
    p = neat.Population(config)
    winner = p.run(eval_genomes)


def eval_genomes(genomes, config):

    gym = PolycraftGym.Gym('127.0.0.1', 9000)
    gym.sock_connect()

    gym.setup_scene('experiments/simple.psm')
    # print(gym.step_command('MOVE_FORWARD'))
    #
    # data = gym.step_command('LOOK_EAST')
    # data_dict = json.loads(data)
    # data_img = data_dict.get('screen').get('img')
    # data_img = np.array(data_dict.get('screen').get('img'), dtype=np.uint32)

    for genome_id, genome in genomes:
        gym.setup_scene('experiments/simple.psm')
        print(gym.step_command('MOVE_FORWARD'))

        obs = json.loads(gym.step_command('LOOK_EAST'))
        net = neat.nn.recurrent.RecurrentNetwork.create(genome, config)

        imgarray = []
        current_max_fitness = 0
        net_reward = 0
        frame = 0
        counter = 0
        xpos = 0
        xpos_max = 0
        done = False
        while not done:
            frame += 1
            data_dict = json.loads(obs)
            data_img = data_dict.get('screen').get('img')
            ob = data_img.view(np.uint8).reshape(data_img.shape+(4,))[..., :3]

            imgarray = np.ndarray.flatten(ob)

            nnOutput = net.activate(imgarray)

            action = env.action_space.noop()

            action['attack'] = nnOutput[0]
            action['back'] = nnOutput[1]
            action['camera'] = [0, (nnOutput[3] * 4) - 1]
            action['forward'] = nnOutput[4]
            action['jump'] = nnOutput[5]
            action['left'] = nnOutput[6]
            # action['place'] = nnOutput[7]
            action['right'] = nnOutput[8]
            action['sneak'] = nnOutput[9]
            action['sprint'] = nnOutput[10]

            obs, reward, done, info = env.step(
                action)

            net_reward += reward
            print("Total reward: ", net_reward)

            if net_reward > current_max_fitness:
                current_max_fitness = net_reward
                counter = 0
            else:
                counter += 1

            if done or counter == 250:
                done = True
                print(genome_id, net_reward)

            genome.fitness = net_reward


if __name__ == '__main__':
    main()


def speed_test(gym):
    millis = int(round(time.time() * 1000))
    gym.step_command('LOOK_NORTH')
    print(millis - int(round(time.time() * 1000)))

