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

if __name__ == "__main__":
    for i in range (14,21):
        compileControl(i)
    # compileControl()
