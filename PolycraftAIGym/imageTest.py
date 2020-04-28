import numpy as np
import json
from matplotlib import pyplot as plt

img_array = []

with open('screenjson.txt') as json_file:
    data = json.load(json_file)
    img_array = np.array(data['screen']['img'], dtype=np.uint32)


    img_array = img_array.view(np.uint8).view(np.uint8).reshape(img_array.shape+(4,))[..., :3]
    img_array = np.reshape(img_array, (256, 256, 3))
    img_array = np.flip(img_array, 0)
    img_array = np.flip(img_array, 2)
    #img_array = np.array(img_array, dtype=np.uint832)


    print(img_array)

    plt.imshow(img_array, interpolation='none')
    plt.show()
