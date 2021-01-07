import numpy as np
import xarray as xr
from glob import glob
import matplotlib
import matplotlib.pyplot as plt

def compileFeedback(n):
    prefix = 'b.e15.B5505C5WCCML45BGCR.f09_g16.feedback.'
    filedir = '/glade/u/home/hayness/glens/feedback'
    n_member = str(n).zfill(3)
    print(n_member)
    print('LOADING FILES')
    filenames = glob('{0}/{1}{2}*.nc'.format(filedir, prefix, n_member))
    filenames.sort()
    start = filenames[0].split('-')[0].split('.')[-1]
    end   = filenames[-1].split('-')[-1].split('.')[0]
    print('LOADING ARRAY')
    da = xr.concat([xr.open_dataset(name)['PRECT'] for name in filenames], dim='time')
    savedir = '/glade/u/home/hayness/glens/custom'
    print('SAVING ARRAY')
    # da.to_netcdf('{0}/{1}{2}.PRECT.{3}-{4}.nc'.format(savedir, prefix, n_member, start, end))
    # print('ARRAY SAVED\n')
    return da

def compileControl():
    prefix = 'b.e15.B5505C5WCCML45BGCR.f09_g16.control.'
    filedir = '/glade/collections/glens/Control/atm/proc/tseries/daily/PRECT'
    ensemble_members = np.arange(1,21)
    for n_member in ensemble_members:
        n_member = str(n_member).zfill(3)
        filenames = glob('{0}/{1}{2}*.nc'.format(filedir, prefix, n_member))
        filenames.sort()
        start = filenames[0].split('-')[0].split('.')[-1]
        end = filenames[-1].split('-')[-1].split('.')[0]
        da = xr.concat([xr.open_dataset(name)['PRECT'] for name in filenames], dim='time')
        savedir = '/glade/u/home/hayness/glens/custom'
        da.to_netcdf('{0}/{1}{2}.PRECT.{3}-{4}.nc'.format(savedir, prefix, n_member, start, end))
    return True

# compileFeedback(3)
# compileControl()
