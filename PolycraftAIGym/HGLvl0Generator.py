import json, random, os, errno, sys, getopt, shutil


class HGLvl0Generator:
    """
        Generator function for Level 0 novelty in Hunter Gatherer Task
    """
    def __init__(self, seed=0, intensity=50,path='../available_tests/hg_nonov.json', output='../output', output_name='hg_lvl-0', args=(), kwargs=None):
        self.seed = seed
        self.intensity = intensity
        self.template_path = path
        self.output = output
        self.output_name = output_name

    def generate(self):
        expDef = None
        # need to copy over the map file as well
        expDefMap = open(self.template_path + '2')
        with open(self.template_path) as f:
            expDef = json.load(f)

        # initialize random with seed
        random.seed(self.seed)

        # set macguffin position
        valid_pos = False
        x1 = random.randint(1, 30)
        z1 = random.randint(1, 30)
        while not valid_pos:
            valid = True
            # macguffin loc should not match macguffin loc
            for jsonFeat in expDef['features']:
                if str(jsonFeat['name']).lower().startswith('wall'):
                    if x1 >= min(int(jsonFeat['pos'][0]), int(jsonFeat['pos2'][0])) and x1 <= max(int(jsonFeat['pos'][0]), int(jsonFeat['pos2'][0])):
                        if z1 >= min(int(jsonFeat['pos'][2]), int(jsonFeat['pos2'][2])) and z1 <= max(int(jsonFeat['pos'][2]), int(jsonFeat['pos2'][2])):
                            valid = False
            if valid:
                valid_pos = True
            else:
                x1 = random.randint(1, 30)
                z1 = random.randint(1, 30)

        for jsonFeat in expDef['features']:
            if str(jsonFeat['name']).startswith('World Builder 8'):
                for block in jsonFeat['blockList']:
                    if str(block['blockDef']['blockName']).startswith('polycraft:macguffin'):
                        block['blockPos'] = [x1, 4, z1]

        # set destination position
        valid_pos = False
        x2 = random.randint(1, 30)
        z2 = random.randint(1, 30)
        while not valid_pos:
            valid = True
            # dest loc should not match wall locations
            for jsonFeat in expDef['features']:
                if str(jsonFeat['name']).lower().startswith('wall'):
                    if x2 >= min(int(jsonFeat['pos'][0]), int(jsonFeat['pos2'][0])) and x2 <= max(
                            int(jsonFeat['pos'][0]), int(jsonFeat['pos2'][0])):
                        if z2 >= min(int(jsonFeat['pos'][2]), int(jsonFeat['pos2'][2])) and z2 <= max(
                                int(jsonFeat['pos'][2]), int(jsonFeat['pos2'][2])):
                            valid = False
            # dest loc should not match macguffin loc
            if x2 == x1 and z2 == z2:
                valid = False
            if valid:
                valid_pos = True
            else:
                x2 = random.randint(1, 30)
                z2 = random.randint(1, 30)

        for jsonFeat in expDef['features']:
            if str(jsonFeat['name']).startswith('End Condition'):
                    jsonFeat['locationToReach'] = [x2, 4, z2]

        #check output dir exists
        if not os.path.exists(os.path.dirname(self.output + '/' + self.output_name + '-' + str(self.seed) + '.json')):
            try:
                os.makedirs(os.path.dirname(self.output + '/' + self.output_name + '-' + str(self.seed) + '.json'))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        # write new experiment config file
        with open(self.output + '/' + self.output_name + '-' + str(self.seed) + '.json', 'w') as json_file:
            json.dump(expDef, json_file, indent=4, sort_keys=True)
        # copy over map data as well
        shutil.copy(self.template_path + '2', self.output + '/' + self.output_name + '-' + str(self.seed) + '.json2')

if __name__ == "__main__":
    argv = sys.argv[1:]
    seed = 0
    intensity = 50
    template_path = '../available_tests/hg_nonov.json'
    output = '../output'
    output_name = 'hg_lvl-0'
    try:
        opts, args = getopt.getopt(argv, "hs:i:t:o:n", ["seed=", "intensity=", "templatePath=", "outputPath=", "outputName="])
    except getopt.GetoptError:
        print
        'HGLvl0Generator.py -s <seed> -i <intensity> -t <template_path> -o <output_path> -n <output_name>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print
            'HGLvl0Generator.py -s <seed> -i <intensity> -t <template_path> -o <output_path> -n <output_name>'
            sys.exit()
        elif opt in ("-s", "--seed"):
            seed = arg
        elif opt in ("-i", "--intensity"):
            intensity = arg
        elif opt in ("-t", "--template-path"):
            template_path = arg
        elif opt in ("-o", "--output-path"):
            output = arg
        elif opt in ("-n", "--output-name"):
            output_name = arg
    gen = HGLvl0Generator(seed=seed, intensity=intensity, path=template_path, output=output, output_name=output_name)
    gen.generate()