################################################################################
# doff_img.py, version 1.0.1
#
# 1.0:
#     - first version
# 1.0.1:
#     - load json config file
#
# Author: Edward Lin hsingwel@umich.edu
################################################################################

import multiprocessing
from astropy.io import fits
from astropy.wcs import WCS
import tensorflow as tf
from scipy.ndimage import zoom
import sys, os, glob
from multiprocessing import Pool
from scipy import ndimage
from scipy.stats import mode
import numpy as np
import time
import subprocess
from subprocess import DEVNULL
import shlex
import shutil
import json

def trim(file0, file1):
    '''
    This function trim image and template to the same size  
    '''
    expnum = file0.split('_')[6]
    img0 = fits.open(file0)
    img1 = fits.open(file1)
    img0_trim = np.zeros((2100,4200)) #center: 1025, 2040
    Y_size, X_size = np.shape(img0[0].data)
    y0_0 = 1050-int(Y_size/2)
    x0_0 = 2100-int(X_size/2)
    y1_0 = y0_0 + Y_size
    x1_0 = x0_0 + X_size
    img0_masked = img0[0].data
    img0_trim[y0_0:y1_0, x0_0:x1_0] += img0_masked
    w0 = WCS(img0[0].header)
    w1 = WCS(img1[0].header)
    ra, dec = w0.wcs_pix2world([2000],[1000],0)
    X, Y = w1.wcs_world2pix(ra,dec,0)
    img1_trim = ndimage.shift(img1[0].data, [y0_0+1000-Y[0], x0_0+2000-X[0]])[:2100, :4200]
    header0 = img0[0].header
    CRPIX1 = header0['CRPIX1']
    CRPIX2 = header0['CRPIX2']
    header0.set('CRPIX1', CRPIX1+x0_0)
    header0.set('CRPIX2', CRPIX2+y0_0)
    header1 = img1[0].header
    CRPIX1= header1['CRPIX1']
    CRPIX2 = header1['CRPIX2']
    header1.set('CRPIX1', CRPIX1+x0_0-X[0]+2000)
    header1.set('CRPIX2', CRPIX2+y0_0+1000-Y[0])
    hdu0 = fits.PrimaryHDU(img0_trim, header0)
    output0 = file0.replace('.fits', '.trim.fits')
    hdu0.writeto(output0)
    hdu1 = fits.PrimaryHDU(img1_trim, header1)
    output1 = file1.replace('.fits', '.{}.trim.fits'.format(time.time()))
    try:
        hdu1.writeto(output1)
    except OSError:
        time.sleep(1)
        output1 = file1.replace('.fits', '.{}.trim.fits'.format(time.time()))
        hdu1.writeto(output1)

    return output0, output1

def diff_img(run_num_list):
    '''
    run image differencing routine
    '''
    #rad_in, rad_tmp, zp, zp_tmp, bg0, bg1, tr0, tr1, inim, tmpim
    run_num, rad_in, rad_tmp, zp, zp_tmp, bg0, bg1, tr0, tr1, inim, tmpim = run_num_list
    img0 = inim
    img1 = tmpim
    rad0 = rad_in
    rad1 = rad_tmp
    img_out = img0.replace('.trim.fits', '.diff.fits')
    params = {0: [600, 1, 0.95], 1: [600, 1, 1], 2: [600, 1, 1.05],
              3: [600, .7, 0.95], 4: [600, .9, .95], 5: [600, 1.1, .95]}
    fluxC, temp_fac, factor = [600, 1, 1] #params[run_num]
    tu = fluxC*rad0**2
    tu_temp = tu / temp_fac
    sigma_match = ((rad0*factor/((2*np.log(2))**0.5))**2 - (rad1/((2*np.log(2))**0.5)))**0.5
    command = 'hotpants -inim {0} -tmplim {1} -outim {2} -tl -1000 -tu {3} -il -1000 -iu {4} -c t -ng 3 6 {6} -r {8} -nsx 10 -nsy 10 -nrx 1 -nry 1 -ko 2 -bgo 1 -sconv'.format(img0, img1, img_out, tu_temp, tu, sigma_match*0.5, sigma_match, sigma_match*2, 3*rad0)
    p0 = subprocess.call(shlex.split(command), stdout=DEVNULL, stderr=DEVNULL)
    return img_out

def cal_flux_radius(img0, img1):
    '''
    calcuate PSF size of image and template
    '''
    #img0_cat = np.loadtxt(img0.replace('.fits', '.cat'))
    #img1_cat = np.loadtxt(img1.replace('.fits', '.cat'))
    #zp = fits.getheader(img0, 1)['MAGZERO'] 
    zp = 28#fits.getheader(img0, 0)['MAGZERO'] 
    zp_tmp = 28#fits.getheader(img1, 0)['MAGZERO'] 
    img0_cat = fits.open(img0.replace('.fits', '.cat'))[1]
    img1_cat = fits.open(img1.replace('.fits', '.cat'))[1]
    FR0 = img0_cat.data['FLUX_RADIUS']
    FR1 = img1_cat.data['FLUX_RADIUS']
    FR0 = FR0[np.logical_and(FR0>1.7, FR0<10)]
    FR1 = FR1[np.logical_and(FR1>1.7, FR1<10)]
    hist0 = np.histogram(FR0, bins=100)
    hist1 = np.histogram(FR1, bins=100)
    BG0 = img0_cat.data['BACKGROUND'].mean()
    BG1 = img1_cat.data['BACKGROUND'].mean()
    Tr0 = img0_cat.data['THRESHOLD'].mean()
    Tr1 = img1_cat.data['THRESHOLD'].mean()
    return (hist0[1][hist0[0].argmax()]+hist0[1][hist0[0].argmax()+1])/2.,\
           (hist1[1][hist1[0].argmax()]+hist1[1][hist1[0].argmax()+1])/2, \
           zp, zp_tmp, BG0, BG1, Tr0, Tr1

def gen_diff(input_image):
    print(input_image)
    field = input_image.split('_')[1]
    ccd = input_image.split('_')[3]
    #tmp = 'NH_{0}_{1}'.format(field, ccd)
    tmp = 'coadd.fits'
    rad_in, rad_tmp, zp, zp_tmp, bg0, bg1, tr0, tr1 = cal_flux_radius(input_image, tmp)
    inim, tmpim = trim(input_image, tmp)
    run_num = [0, rad_in, rad_tmp, zp, zp_tmp, bg0, bg1, tr0, tr1, inim, tmpim]
    dimg = [diff_img(run_num)]
    return dimg

def zp_cut(img_list):
    zp = np.zeros(len(img_list))
    for n, l in enumerate(img_list):
        zp[n] +=  fits.getheader(l, 1)['MAGZERO']
        #zp[n] +=  fits.getheader(l, 0)['MAGZERO']
        cat = l.replace('.fits', '.cat')
        img0_cat = fits.open(cat)[1].data['FLUX_RADIUS']
        img0_cat = img0_cat[np.logical_and(img0_cat>1.7, img0_cat<10)]
    
    zp_cut = zp > 28#(zp.mean()-1.5*zp.std())   
    return np.array(img_list)[zp_cut]   

def read_fits_img(data):
    if data.endswith('fz'):
        img = fits.open(data)[1].data[100:2000, 150:4050]
    else:
        img = fits.open(data)[0].data[100:2000, 150:4050]
    img[np.isnan(img)] = -10E-30
    img[np.isinf(img)] = -10E-30
    img = zoom(img, 0.1)
    img[img>30] = 30
    img[img< -30] = -30
    img += 30
    img /= 60
    return np.array([img]).reshape(190,130,3, order='F')

def check_img(img_list):
    '''
    check differencing images
    '''
    imgs = list(map(read_fits_img, img_list))
    deep_check_imgs = np.array(imgs)
    print(deep_check_imgs.shape)
    deep_check_result = deep_check.predict(deep_check_imgs)
    return deep_check_result.flatten()

def main():
    global deep_check
    pool = multiprocessing.Pool(processes=4)
    conf = json.load(open('/data7/DEEP/python/config.json'))
    deep_check = tf.keras.models.load_model(conf["ML_model"])
    img_list = open('img.list').readlines()
    img_list = [i.strip() for i in img_list]
    list(pool.map(gen_diff, img_list))
    trim_files = glob.glob('*trim*fits')
    for i in trim_files:
        os.remove(i)
    diff_img_list = glob.glob('*.diff.fits')
    check_result = check_img(diff_img_list)
    diff_img_list = np.array(diff_img_list)
    check_result = np.array(check_result)
    for n, j in enumerate(diff_img_list):
        print('{}: {}'.format(j, check_result[n]))
        if check_result[n] > -7:
            fits.setval(j, 'ml_score', value=check_result[n])
        else:
            os.remove(j)
           
if __name__ == '__main__':
    main()
