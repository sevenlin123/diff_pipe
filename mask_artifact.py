import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import glob
import json

def read_gaia():
    conf = json.load(open('/data7/DEEP/python/config.json'))
    gaia = fits.open(conf['gaia'])[1].data
    #gaia = fits.open('Gaia_04_A0b.fits.fz')[1].data
    return gaia['ra'], gaia['dec'], gaia['phot_g_mean_mag']

def cal_flux_radius(img0):
    img0_cat = fits.open(img0.replace('.diff.fits', '.cat'))[1]
    FR0 = img0_cat.data['FLUX_RADIUS']
    FR0 = FR0[np.logical_and(FR0>1.7, FR0<10)]
    hist0 = np.histogram(FR0, bins=100)
    rad = (hist0[1][hist0[0].argmax()]+hist0[1][hist0[0].argmax()+1])/2.
    return rad

def read_coadd():
    coadd_cat = fits.open('coadd.cat')[1]
    mask = (coadd_cat.data['MAG_AUTO'] != 99)
    FR1 = coadd_cat.data['FLUX_RADIUS'][mask]
    FR1 = FR1[np.logical_and(FR1>1.7, FR1<10)]
    hist1 = np.histogram(FR1, bins=100)
    rad_coadd = (hist1[1][hist1[0].argmax()]+hist1[1][hist1[0].argmax()+1])/2.
    thr = coadd_cat.data['THRESHOLD'][0]
    flux_mask = (coadd_cat.data['FLUX_AUTO'] > 1000*thr)
    RA = coadd_cat.data['X_WORLD'][flux_mask]
    DEC = coadd_cat.data['Y_WORLD'][flux_mask]
    return rad_coadd, RA, DEC

def cal_rad(mag):
    mag0 = 21
    delta_mag = mag0 - mag
    delta_mag[delta_mag < 0 ] = 0
    r = lambda delta_mag:(-np.log(1/(2.512**delta_mag))+1)**0.5
    rad = r(delta_mag)*(1+0.4*delta_mag)+2
    rad[mag == 22.0] = 2
    return rad

def mask(img_file):
    comsic_ray_mask = img_file.replace('.fits', '.mask.fits')
    cr_mask = fits.open(comsic_ray_mask)[0].data.astype(bool)
    rad0 = cal_flux_radius(img_file)
    print('{}: radius = {}'.format(img_file, rad0))
    with fits.open(img_file, mode='update') as img:
        w0 = WCS(img[0].header)
        x, y = w0.wcs_world2pix(ra,dec,0)
        effective = (x>50) & (x<4150) & (y>50) & (y<2050)
        x_eff = x[effective].round().astype(int)
        y_eff = y[effective].round().astype(int)
        mag_eff = mag[effective]
        rad = (cal_rad(mag_eff) * rad0).round().astype(int)
        imgmask = np.zeros(img[0].data.shape, dtype=bool)
        for i in range(-rad.max(), rad.max()):
            for j in range(-rad.max(),rad.max()):
                x_apply = x_eff[(rad**2 >= i**2+j**2)] + i
                y_apply = y_eff[(rad**2 >= i**2+j**2)] + j
                x_apply[x_apply > 4199] = 4199
                x_apply[x_apply < 0] = 0
                y_apply[y_apply > 2099] = 2099
                y_apply[y_apply < 0] = 0
                imgmask[y_apply, x_apply] = 1
        
        img[0].data[imgmask] = 0
        img[0].data[cr_mask] = 0
        img.flush()
    
def main():
    global ra, dec, mag, rad_coadd
    img_list = glob.glob('*fakes.diff.fits')
    ra, dec, mag = read_gaia()
    rad_coadd, ra_coadd, dec_coadd = read_coadd()
    ra = np.concatenate((ra,ra_coadd))
    dec = np.concatenate((dec,dec_coadd))
    mag = np.concatenate((mag, np.zeros(len(ra_coadd))+22))  
    #for i in zip(ra, dec):
    #    print('{} {}'.format(i[0], i[1]))
    list(map(mask, img_list))

if __name__ == '__main__':
    main()
