import os, glob
from astropy.io import fits
import numpy as np
import json
import subprocess
from subprocess import DEVNULL
import shutil


conf = json.load('config.json')
root = conf["root"]
os.chdir(root)
date_list = glob.glob(conf["run"])
date_list = filter(lambda x: not x.endswith('gz'), date_list)
for i in date_list:
    os.chdir(root+i)
    field_list = glob.glob(conf["field"])
    for j in field_list:
        os.chdir(root+i+'/'+j)
        ccd_list = glob.glob(conf["ccd"])
        for k in ccd_list:
            os.chdir(root+i+'/'+j+'/'+k)
            print(root+i+'/'+j+'/'+k)
            #print('swarp *.fits')
            shutil.copy('{}python/default.swarp'.format(root), '.')
            img_list = glob.glob('c4d*CCD?.fits') + glob.glob('c4d*CCD??.fits')
            zp = np.zeros(len(img_list))
            rad = np.zeros(len(img_list))
            for n, l in enumerate(img_list):
                zp[n] +=  fits.getheader(l, 1)['MAGZERO']
                cat = l.replace('.fits', '.cat')
                img0_cat = fits.open(cat)[1].data['FLUX_RADIUS']
                img0_cat = img0_cat[np.logical_and(img0_cat>1.7, img0_cat<10)]
                hist0 = np.histogram(img0_cat, bins=100)
                rad[n] += (hist0[1][hist0[0].argmax()]+hist0[1][hist0[0].argmax()+1])/2.
            print(zp.min(), zp.mean(), zp.max(), zp.std())
            print(rad.min(), rad.mean(), rad.max(), rad.std())
            zp_cut = zp < (zp.mean()-2*zp.std())
            zp_eff = zp[~zp_cut]
            zp_ref = zp_eff.min()
            zp_diff = zp_eff - zp_ref
            f_diff = 10**(zp_diff/2.5)
            ZERO = zp_ref + 2.5*np.log10(f_diff.mean())
            ZERO = round(ZERO, 3)
            command = 'swarp '
            for l in (np.array(img_list)[~zp_cut]):
                command += '{} '.format(l)
            
            #print(command)
            p0 = subprocess.call(command)
            coadd_img = fits.setval('coadd.fits', 'MAGZERO', value=ZERO)
            os.rename('coadd.fits', '{}_{}_{}.fits'.format(i, j, k))
            fits.setval('{}_{}_{}.fits'.format(i, j, k), 'MAGZERO', value=ZERO)


for i in date_list:
    os.chdir(root+i)
    field_list = glob.glob(conf["field"])
    for j in field_list:
        os.chdir(root+i+'/'+j)
        ccd_list = glob.glob(conf["ccd"])
        for k in ccd_list:
            os.chdir(root+i+'/'+j+'/'+k)
            print(root+i+'/'+j+'/'+k)
            tmp_date = run_list.copy()
            tmp_date.remove(i)
            print(tmp_date)
            for l in tmp_date:
                shutil.copy('{}/{}/{}/{}/{}*fits'.format(root, l, j, k, l), '.')
            
            p0 = subprocess.call('swarp 20*fits')
            img_list = glob.glob('20*fits')
            ZERO = np.zeros(len(img_list))
            for n,l in enumerate(img_list):
                ZERO[n] += fits.getval(l, 'MAGZERO')

            zp_ref = ZERO.min()
            zp_diff = ZERO - zp_ref
            f_diff = 10**(zp_diff/2.5)
            ZP = zp_ref + 2.5*np.log10(f_diff.mean())
            p1 = subprocess.call('sex coadd.fits')
            coadd_img = fits.setval('coadd.fits', 'MAGZERO', value=ZP)
            os.rename('test.cat', 'coadd.cat')            
