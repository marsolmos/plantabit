import os
import random
from scipy import ndarray

# image processing library
import skimage as sk
from skimage import transform
from skimage import util
from skimage import io

def random_rotation(image_array: ndarray):
    # pick a random degree of rotation between 25% on the left and 25% on the right
    random_degree = random.uniform(-25, 25)
    return sk.transform.rotate(image_array, random_degree)

def random_noise(image_array: ndarray):
    # add random noise to the image
    return sk.util.random_noise(image_array)

def horizontal_flip(image_array: ndarray):
    # horizontal flip doesn't need skimage, it's easy as flipping the image array of pixels !
    return image_array[:, ::-1]

# dictionary of the transformations we defined earlier
available_transformations = {
    'rotate': random_rotation,
    'noise': random_noise,
    'horizontal_flip': horizontal_flip
}

folders = ['train', 'test', 'validation']
species = [
          'Chlorophytum comosum', 'Epipremnum aureum',
          'Cordyline australis', 'Spathiphyllum',
          'Sansevieria zeylanica', 'Crassuwa ovata',
          'Anthurium', 'Ficus lyrata',
          'Monstera adansonii', 'Monstera deliciosa',
          'Howea forsteriana', 'Aloe barbadensis miller'
          ]
for f in folders:
    if f == 'train':
        num_files_desired = 720
    elif f == 'validation':
        num_files_desired = 180
    elif f == 'test':
        num_files_desired = 100
    for s in species:
        folder_path = 'D:\\Data Warehouse\\plantabit\\3_rawdata_clean_no_duplicates_aug\\{}\\{}'.format(f, s)

        # find all files paths from the folder
        images = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        num_generated_files = 0
        while num_generated_files <= num_files_desired:
            # random image from the folder
            image_path = random.choice(images)
            if 'augmented_image_' in image_path:
                pass
            else:
                # read image as an two dimensional array of pixels
                print('\nTransforming image: {}'.format(image_path))
                image_to_transform = sk.io.imread(image_path)
                # random num of transformation to apply
                num_transformations_to_apply = random.randint(1, len(available_transformations))

                num_transformations = 0
                transformed_image = None
                while num_transformations <= num_transformations_to_apply:
                    # random transformation to apply for a single image
                    key = random.choice(list(available_transformations))
                    transformed_image = available_transformations[key](image_to_transform)
                    num_transformations += 1

                    new_file_path = '%s/augmented_image_%s.png' % (folder_path, num_generated_files)

                    # write image to the disk
                    io.imsave(new_file_path, transformed_image)
                num_generated_files += 1
