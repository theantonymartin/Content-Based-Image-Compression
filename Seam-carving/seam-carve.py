import argparse
import os
import math
import numpy as np
from PIL import Image
from imageio import imread, imwrite
from scipy.ndimage.filters import convolve
def find_energy(image):
	# image = image.convert('F')
	image = image.astype('float32')
	print(np.max(np.array(image)))
	dx = np.array([
        [1.0, 2.0, 1.0],
        [0.0, 0.0, 0.0],
        [-1.0, -2.0, -1.0],
    ])
	dy = np.array([[1.0, 0.0, -1.0],
		[2.0, 0.0, -2.0],
		[1.0, 0.0, -1.0],])
	dx = np.stack([dx]*3, axis = 2)
	dy = np.stack([dy]*3, axis = 2)
	print(image.shape)
	print(dx.shape)
	convx = convolve(image,dx)
	convy = convolve(image,dy)
	# E_map = np.sum(np.absolute(convx + convy), axis = 2)
	E_map = np.absolute(convx) + np.absolute(convy)
	return E_map.sum(axis = 2)

def seam_map(image):
	s1, s2= image.shape[:2]
	T = find_energy(image)
	path = np.zeros((s1,s2), dtype = np.int)
	for i in range(1, s1):
		# print(i)
		for j in range(0, s2):
			if j==0:
				path[i,j] = j + np.argmin(T[i-1, j:j+2])
			elif j==s2-1:
				path[i,j] = j + np.argmin(T[i-1, j-1:j+1]) - 1
			else:
				path[i,j] = j + np.argmin(T[i-1, j-1:j+2]) - 1
			# print(path[i,j])
			E = T[i-1, path[i,j]]
			T[i,j]+=E
	return T, path

def cut_path(image):
	s1 = image.shape[0]
	s2 = image.shape[1]
	T, path = seam_map(image)
	M = np.ones((s1,s2), dtype = np.bool)
	min_index = np.argmin(T[s1-1])
	for i in range(s1 -1, -1, -1):
		M[i,min_index] = False
		min_index = path[i,min_index]
	M = np.stack([M]*3, axis = 2)
	image = image[M].reshape(s1, s2-1,3)
	return image



def main():
    print("Hello")
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="path to the input image")
    parser.add_argument("output", help="path to the output image")
    parser.add_argument("xscale", help="Horizontal Scale")
    parser.add_argument("yscale", help="Vertical Scale")
    args = parser.parse_args()
    print(args)
    input_file = args.input
    output_file = args.output
    x_scale = args.xscale
    y_scale = args.xscale
    image = imread(input_file)
    s1 = image.shape[0]
    s2 = image.shape[1]
    new_s1 = int(s1*float(y_scale))
    new_s2 = int(s2*float(x_scale))
    print(new_s1, new_s2)
    for i in range(s2 - new_s2):
    	image = cut_path(image)

    for i in range(s1 - new_s1):
        image = np.rot90(image)
        image = cut_path(image)
        image = np.rot90(image, 3)
    imwrite(output_file, image)

if __name__ == "__main__":
    main()

    # npmat = np.array(ycbcr, dtype=np.uint8)

    # rows, cols = npmat.shape[0], npmat.shape[1]

    # # block size: 8x8
    # if rows % 8 == cols % 8 == 0:
    #     blocks_count = rows // 8 * cols // 8
    # else:
    #     raise ValueError(("the width and height of the image "
    #                       "should both be mutiples of 8"))

    # # dc is the top-left cell of the block, ac are all the other cells
    # dc = np.empty((blocks_count, 3), dtype=np.int32)
    # ac = np.empty((blocks_count, 63, 3), dtype=np.int32)