import os, glob
from astropy.io import fits
import json
import subprocess
from subprocess import DEVNULL
import shutil
import shlex

conf = json.load('config.json')
root = conf['root']
os.chdir(root)
#date_list = glob.glob('20190507')
date_list = glob.glob('{}/{}/{}/'.format(conf['fakes'], conf['field'], conf['date']))
date_list = filter(lambda x: not x.endswith('gz'), date_list)
for i in date_list:
    os.chdir(root+i)
    #field_list = glob.glob('A0c')
    field_list = glob.glob('.')
    for j in field_list:
        os.chdir(root+i+'/'+j)
        ccd_list = glob.glob(conf['ccd'])# + glob.glob('ccd*')
        #ccd_list = ['CCD62']
        for k in ccd_list:
            os.chdir(root+i+'/'+j+'/'+k)
            print(root+i+'/'+j+'/'+k)
            shutil.copy('{}python/default.sex'.format(root), '.')
            shutil.copy('{}python/default.param'.format(root), '.')
            shutil.copy('{}python/default.conv'.format(root), '.')
            os.remove('coadd.weight.fits')
            fits_list = glob.glob('c4d*fakes.fits')
            #fits_list = glob.glob('2019*0507*.fits')
            for l in fits_list:
                print(l)
                cat = l.replace('fits', 'cat')
                #zp = fits.getheader(l, 1)['MAGZERO'] 
                try:
                    zp = fits.getheader(l, 0)['MAGZERO']
                except OSError:
                    zp = 0
                subimg = l.replace('fits', 'sub.fits')
                if os.path.isfile(cat) == False: 
                    command = 'sex -CATALOG_NAME {} -MAG_ZEROPOINT {} -CHECKIMAGE_TYPE NONE {}'.format(cat, zp, l))
                    p0 = subprocess.call(shlex.split(command))


