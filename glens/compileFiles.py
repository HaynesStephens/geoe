import numpy as np
import xarray as xr
from glob import glob
import pandas as pd
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
    print('Shifting')
    da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180))
    da = da.sortby(da.lon)
    print('Cropping')
    da = da.sel(lat=slice(lats[0], lats[1]), lon=slice(lons[0], lons[1]))  # Select the region
    return da


def cropFiles(region):
    filedir = '/glade/work/hayness/glens/custom'
    filenames = glob('{0}/*.nc'.format(filedir))
    for filename in filenames:
        print('Loading:')
        print(filename)
        da = xr.open_dataarray(filename)
        da = cropRegion(da, region)
        savename = filedir + '/{0}/'.format(region) + filename.split('/')[-1][:-2] + '{0}.nc'.format(region)
        print('Saving:')
        print(savename)
        da.to_netcdf(savename)
        print('Saved! \n')


def getEnsembleMean(scen, region=None):
    print(scen)
    print(region)
    filedir = '/glade/work/hayness/glens/custom'
    con_files = ['b.e15.B5505C5WCCML45BGCR.f09_g16.control.001.PRECT.20100101-20990630.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.002.PRECT.20100101-20980811.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.003.PRECT.20100101-21000630.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.004.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.005.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.006.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.007.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.008.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.009.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.010.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.011.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.012.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.013.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.014.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.015.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.016.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.017.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.018.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.019.PRECT.20100101-20301231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.020.PRECT.20100101-20301231.']
    rcp_files = ['b.e15.B5505C5WCCML45BGCR.f09_g16.control.001.PRECT.20100101-20990630.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.002.PRECT.20100101-20980811.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.003.PRECT.20100101-21000630.']
    geo_files = ['b.e15.B5505C5WCCML45BGCR.f09_g16.feedback.001.PRECT.20200101-20991231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.feedback.002.PRECT.20200101-20991231.',
                 'b.e15.B5505C5WCCML45BGCR.f09_g16.feedback.003.PRECT.20200101-20991231.']
    file_dict = {'control':con_files,
                 'rcp': rcp_files,
                 'feedback': geo_files}
    year_dict = {'control': ('2010', '2030'),
                 'rcp': ('2010', '2100'),
                 'feedback': ('2020', '2099')}
    savename_dict = {'control': 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.ensemble.PRECT.20100101-20301231.',
                     'rcp': 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.ensemble.PRECT.20100101-21000630.',
                     'feedback': 'b.e15.B5505C5WCCML45BGCR.f09_g16.feedback.ensemble.PRECT.20200101-20991231.'}
    filenames = file_dict[scen]
    start, end = year_dict[scen]
    savename = savename_dict[scen]
    if region != None:
        filedir = filedir + '/' + region
        filenames = ['{0}{1}.nc'.format(name, region) for name in filenames]
        savename = '{0}{1}.nc'.format(savename, region)
    else:
        filenames = ['{0}nc'.format(name) for name in filenames]
        savename = '{0}nc'.format(savename)
    filenames = ['{0}/{1}'.format(filedir, name) for name in filenames]
    savename  = '{0}/{1}'.format(filedir, savename)
    print('Loading:')
    da = xr.merge([xr.open_dataarray(name).sel(time=slice(start, end)).expand_dims({'case': np.arange(i, i + 1)}) for i, name in enumerate(filenames)])
    print('Saving:')
    print(savename)
    da.to_netcdf(savename)
    print('Saved! \n')


if __name__ == "__main__":
    # regions = ['SoAs', 'WeAf']
    # scens = ['control', 'rcp', 'feedback']
    # for region in regions:
    #     for scen in scens:
    region = 'SoAs'
    scen   = 'rcp'
    getEnsembleMean(scen, region)
