import numpy as np
import xarray as xr
from glob import glob
import matplotlib
import matplotlib.pyplot as plt


def compileFiles(n, prefix, filedir):
    n_member = str(n).zfill(3)
    print(n_member)
    print('LOADING FILES')
    filenames = glob('{0}/{1}{2}*.nc'.format(filedir, prefix, n_member))
    filenames.sort()
    start = filenames[0].split('-')[0].split('.')[-1]
    end   = filenames[-1].split('-')[-1].split('.')[0]
    print('LOADING ARRAY')
    da = xr.concat([xr.open_dataset(name)['PRECT'] for name in filenames], dim='time')
    savedir = '/glade/work/hayness/glens/custom'
    print('SAVING ARRAY')
    da.to_netcdf('{0}/{1}{2}.PRECT.{3}-{4}.nc'.format(savedir, prefix, n_member, start, end))
    print('ARRAY SAVED\n')
    return True


def compileFeedback(n):
    prefix = 'b.e15.B5505C5WCCML45BGCR.f09_g16.feedback.'
    filedir = '/glade/work/hayness/glens/feedback'
    return compileFiles(n, prefix, filedir)


def compileControl(n):
    prefix = 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.'
    filedir = '/glade/collections/glens/Control/atm/proc/tseries/daily/PRECT'
    return compileFiles(n, prefix, filedir)


def cropRegion(da, region, lats=None, lons=None):
    coords = {'SoAs':[(-10, 40), (40, 140)], 'WeAf':[(-20, 20), (20, 20)]}
    if (lats==None) & (lons==None):
        lats, lons = coords[region]
    print('Load + Shift')
    da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180))
    da = da.sortby(da.lon)
    print('Crop')
    da = da.sel(lat=slice(lats[0], lats[1]), lon=slice(lons[0], lons[1]))  # Select the region
    return da


def cropSoAs():
    region = 'SoAs'
    filedir = '/glade/work/hayness/glens/custom'
    filenames = glob('{0}/*.nc'.format(filedir))
    for filename in filenames:
        da = xr.open_dataarray(filename)
        da = cropRegion(da, region)
        savename = filedir + '/{0}/'.format(region) + filename.split('/')[-1][:-2] + '{0}.nc'.format(region)
        print('Saving:')
        print(savename)
        da.to_netcdf(savename)


if __name__ == "__main__":
    for i in range (14,21):
        compileControl(i)
    # compileControl()
