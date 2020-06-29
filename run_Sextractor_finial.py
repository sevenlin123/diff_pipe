import os, glob
from astropy.io import fits
import json
import shlex
import subprocess

conf = json.load(open('config.json'))
root = conf['root']
os.chdir(root)
#date_list = glob.glob('20190402')
#date_list = glob.glob('With_Fakes/A0b/20190402/')
ate_list = glob.glob('{}/{}/{}/'.format(conf['fakes'], conf['field'], conf['date']))
date_list = filter(lambda x: not x.endswith('gz'), date_list)
for i in date_list:
    os.chdir(root+i)
    field_list = glob.glob('.')
    for j in field_list:
        #print(j)
        os.chdir(root+i+'/'+j)
        ccd_list = glob.glob(conf['ccd'])
        #ccd_list = ['CCD62']
        for k in ccd_list:
            os.chdir(root+i+'/'+j+'/'+k)
            print(root+i+'/'+j+'/'+k)
            #print(glob.glob('*.diff.fits'))
            fits_list = [i.rstrip('diff.fits') for i in glob.glob('*.diff.fits')]
            sub_fits = [i.rstrip('.diff.sub.fits') for i in glob.glob('*.diff.sub.fits')]
            #fits_list = [i for i in fits_list if i not in sub_fits]
            for l in fits_list:
                print(l)
                #zp = fits.getheader('{}.diff.fits'.format(l), 1)['MAGZERO']
                zp = fits.getheader('{}s.diff.fits'.format(l), 0)['MAGZERO']
                cat = '{}s.diff.1.cat'.format(l)
                subimg = '{}s.diff.sub.fits'.format(l)
                command = 'sex -DETECT_THRESH 3.0 -CATALOG_NAME {} -CHECKIMAGE_TYPE NONE  -MAG_ZEROPOINT {} {}s.diff.fits'.format(cat, zp, l)
                p0 = subprocess.call(shlex.split(command))