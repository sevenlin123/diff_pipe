import os, glob
from astropy.io import fits
import numpy as np
import json
import subprocess
from subprocess import DEVNULL
import shutil

conf = json.load(open('config.json'))
root = conf["root"]
os.chdir(root)
date_list = glob.glob('{}/{}/{}/'.format(conf['fakes'], conf['field'], conf['date']))
date_list = list(filter(lambda x: not x.endswith('gz'), date_list))

for i in date_list:
    os.chdir(root+i)
    field_list = glob.glob('.')
    for j in field_list:
        os.chdir(root+i+'/'+j)
        ccd_list = glob.glob(conf['ccd'])
        for k in ccd_list:
            os.chdir(root+i+'/'+j+'/'+k)
            shutil.copy('{}/{}/{}/{}/coadd.fits'.format(root, conf['date'], conf['field'], k), '.')
            shutil.copy('{}/{}/{}/{}/coadd.cat'.format(root, conf['date'], conf['field'], k), '.')
            img_list = glob.glob('c4d*CCD*fakes.fits')
            with open('img.list', 'w') as output:
               for l in img_list:
                  output.write('{}\n'.format(l))

            shutil.copy('{}/python/diff_img.py'.format(root), '.')
            for l in glob.glob('*.trim*'):
                os.remove(l)
            
            p0 = subprocess.call(['python', '-W', 'ignore', 'diff_img.py'])
