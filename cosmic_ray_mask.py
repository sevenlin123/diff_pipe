################################################################################
# cosmic_ray_mask.py, version 1.0
#
#  create cosmic ray mask 
#
# 1.0:
#     - first version
#
# Author: Edward Lin hsingwel@umich.edu
################################################################################

from matplotlib import pyplot as plt
from astropy.io import fits
import numpy as np
import glob
from scipy.spatial import cKDTree as KDTree
from astropy.wcs import WCS


def read_cat(cat):
    tab = fits.open(cat)
    ra = tab[1].data['X_WORLD']
    dec = tab[1].data['Y_WORLD']
    return KDTree(list(zip(ra,dec)))
    
def prep_mask(input):
    mask_img, cat, remove = input
    output = cat.replace('.cat', '.mask.fits')
    print(mask_img)
    tab = fits.open(cat)
    X = tab[1].data['XWIN_IMAGE']
    Y = tab[1].data['YWIN_IMAGE']
    X = X[remove].round().astype(int)
    Y = Y[remove].round().astype(int)
    acceptable = (X < 4150) & (X > 50) & (Y < 2050) & (Y > 50)
    X = X[acceptable]
    Y = Y[acceptable]
    img = fits.open(mask_img)
    rad = 25
    imgmask = np.zeros(img[0].data.shape, dtype=bool)
    for i in range(-rad, rad):
        for j in range(-rad,rad):
            x_apply = X[(rad**2 >= i**2+j**2)]
            y_apply = Y[(rad**2 >= i**2+j**2)]  
            imgmask[y_apply+j, x_apply+i] = 1
    mask = img[0].data.astype('bool') & imgmask
    hdu = fits.PrimaryHDU(mask.astype(int))
    hdul = fits.HDUList([hdu])
    hdu.writeto(output, overwrite=True)
    


def main():
    diff_list = glob.glob('*.diff.fits')
    cat_list = [i.replace('.fits', '.cat') for i in diff_list]
    mask_img_list = [i.replace('.fits', '.sub.fits') for i in diff_list]
    output_list = [i.replace('.fits', '.mask.fits') for i in diff_list]
    tree_list = list(map(read_cat, cat_list))
    remove_list = [None] * len(tree_list)
    for m, i in enumerate(tree_list):
        test_list = tree_list.copy()
        test_list.remove(i)
        result = [None] * len(test_list)
        for n, j in enumerate(test_list):
            hit = i.query_ball_tree(j, r=5/3600.)
            result[n] = np.array(hit).astype('bool')
        remove_list[m] = np.sum(np.array(result).astype(int), axis=0) < 3
    
    input_info = list(zip(mask_img_list, cat_list, remove_list))
    mask_list = list(map(prep_mask, input_info))
    
if __name__ == '__main__':
    main()
  
    