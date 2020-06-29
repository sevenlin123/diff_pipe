import os, glob
from astropy.io import fits
from subprocess import DEVNULL
import shutil
import shlex
import json

conf = json.load('config.json')
root = conf["root"]
os.chdir(root)
date_list = glob.glob('{}/{}/{}/'.format(conf['fakes'], conf['field'], conf['date']))
date_list = filter(lambda x: not x.endswith('gz'), date_list)
for i in date_list:
    os.chdir(root+i)
    field_list = glob.glob('.')
    for j in field_list:
        os.chdir(root+i+'/'+j)
        ccd_list = glob.glob(conf['ccd'])
        for k in ccd_list:
            os.chdir(root+i+'/'+j+'/'+k)
            print(root+i+'/'+j+'/'+k)
            shutil.copy('{}/python/cosmic_ray_mask.py'.format(root), '.')
            shutil.copy('{}/python/mask_artifact.py'.format(root), '.')
            p0 = subprocess.call('python cosmic_ray_mask.py')
            p1 = subprocess.call('python -W ignore mask_artifact.py')
