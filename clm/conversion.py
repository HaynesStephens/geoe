# Import the necessary libraries
import os
from glob import glob
import numpy as np
import pandas as pd
import xarray as xr

"""
=============================================
How to process CLM5crop output to crop yield
=============================================

=============================================
1. Original crop yield output:
=============================================
Under h1 files:
$CASE/lnd/hist/*h1*

Variable:
GRAINC_TO_FOOD

dimension:
(time-monthly,pft)

=============================================
2. Regrid pft-level data from the 1D output and output a netCDF file with (year,cropPFT,lat,lon)
=============================================
***input variables:
float GRAINC_TO_FOOD(time, pft) ;
                GRAINC_TO_FOOD:long_name = "grain C to food" ;
                GRAINC_TO_FOOD:units = "gC/m^2/s" ;
                GRAINC_TO_FOOD:cell_methods = "time: mean" ;
                GRAINC_TO_FOOD:_FillValue = 1.e+36f ;
                GRAINC_TO_FOOD:missing_value = 1.e+36f ;

int pfts1d_ixy(pft) ;
                pfts1d_ixy:long_name = "2d longitude index of corresponding pft" ;

int pfts1d_jxy(pft) ;
                pfts1d_jxy:long_name = "2d latitude index of corresponding pft" ;

double pfts1d_wtgcell(pft) ;
                pfts1d_wtgcell:long_name = "pft weight relative to corresponding gridcell" ;

float area(lat, lon) ;
                area:long_name = "grid cell areas" ;
                area:units = "km^2" ;
                area:_FillValue = 1.e+36f ;
                area:missing_value = 1.e+36f ;

float landfrac(lat, lon) ;
                landfrac:long_name = "land fraction" ;
                landfrac:_FillValue = 1.e+36f ;
                landfrac:missing_value = 1.e+36f ;


***convert GRAINC_TO_FOOD(mon,pft) to GRAINC_TO_FOOD(mon,PFT,lat,lon) (where pft exists) using ixy and jxy

***sum up monthly data to annual, and mutiply 60*60*24*30*0.85*10/(1000*0.45). After the conversion, "gC/m^2/s" is changed to "ton/ha/yr"

***output the netCDF file with new GRAINC_TO_FOOD, and landarea (area*landfrac)

=============================================
3. remap cropPFT to 8 active crop types
=============================================
***input files and variables:

from the new generated file:
GRAINC_TO_FOOD(annual,PFT,lat,lon)
area(lat,lon)

from land surface file (e.g. /glade/p/univ/urtg0006/Yaqiong/surfdata_0.9x1.25_78pfts_CMIP6_simyr1850_c170824_ggcmi.nc):
double PCT_CFT(cft, lsmlat, lsmlon) ;
                PCT_CFT:long_name = "percent crop functional type on the crop landunit (% of landunit)" ;
                PCT_CFT:units = "unitless" ;

double PCT_CROP(lsmlat, lsmlon) ;
                PCT_CROP:long_name = "total percent crop landunit" ;
                PCT_CROP:units = "unitless" ;

***

calculate cropping area for specific crops using area, PCT_CFT, and PCT_CROP

***

extract 8 active crops from cpt (number starts from 0)

cornrain 2, 60 (one is tropical, the other is temperate)
cornirr 3, 61
soyrain 8, 62
soyirr 9, 63
ricerain 46
riceirr 47
springwheatrain 4
springwheatirr 5
cottonrain 26
cottonirr 27
sugarcanerain 52
sugarcaneirr 53

***

output crop yields and crop area
"""


def Step1(grainc, start_date, end_date, save_name, save_file=True):
    savedir = '/glade/work/hayness/clm/step1'
    grain = grainc.GRAINC_TO_FOOD
    grain = grain.assign_coords(time=pd.date_range(start=start_date, end=str(int(end_date)+1), freq='1M'))

    pfts1d_ixy = grainc.pfts1d_ixy
    pfts1d_jxy = grainc.pfts1d_jxy
    pfts1d_wtgcell = grainc.pfts1d_wtgcell
    pfts1d_itype_veg = grainc.pfts1d_itype_veg
    area = grainc.area
    landfrac = grainc.landfrac
    land_area = area * landfrac

    # Assign PFT coordinate to veg-type data
    pfts1d_itype_veg = pfts1d_itype_veg.assign_coords(pft=pfts1d_itype_veg.pft)

    # Resample grain to yearly sums
    grain = grain.resample(time='1A').sum()

    # Create empty 4D array to construct from 1D GRAINC array
    dims = ['time', 'pft', 'lat', 'lon']
    coords = {'time': grain.time, 'pft': np.arange(pfts1d_itype_veg.max() + 1), 'lat': grainc.lat, 'lon': grainc.lon}
    grain4d = xr.DataArray(dims=dims, coords=coords)

    # Run for loop over 1D array to fill in 4D array
    for pft in grainc.pft.values:
        if (pfts1d_wtgcell.isel(pft=pft) > 0.0):
            veg = int(pfts1d_itype_veg.isel(pft=pft).item())
            lat = int(pfts1d_jxy.isel(pft=pft).item() - 1)
            lon = int(pfts1d_ixy.isel(pft=pft).item() - 1)
            grain4d[dict(pft=veg, lat=lat, lon=lon)] = grain.sel(pft=pft)

    # Change units to ton/ha
    grain4d = grain4d * ((60 * 60 * 24 * 30 * 0.85 * 10) / (1000 * 0.45))
    grain4d.attrs["units"] = "ton/ha/yr"

    if save_file:
        # Save filled-in array as is
        grain4d.to_netcdf(savedir + '/HAYNES.{0}'.format(save_name))

    return grain4d, land_area


def Step2(surf_data, grain4d, land_area, save_name):
    savedir = '/glade/work/hayness/clm/step2'
    pct_crop = surf_data.PCT_CROP
    pct_cft = surf_data.PCT_CFT

    # Create empty 4D array to construct YIELD_OUT by CROP
    dims = ['cft', 'time', 'lat', 'lon']
    cft_coord = pct_cft.cft - 15.0
    coords = {'time': grain4d.time, 'cft': cft_coord, 'lat': grain4d.lat, 'lon': grain4d.lon}
    yield_OUT = xr.DataArray(dims=dims, coords=coords).rename('yield')
    yield_OUT.attrs["units"] = "ton/ha/yr"

    # Create empty 3D array to construct AREA_OUT by CROP
    dims = ['cft', 'lat', 'lon']
    coords = {'cft': cft_coord, 'lat': grain4d.lat, 'lon': grain4d.lon}
    area_OUT = xr.DataArray(dims=dims, coords=coords).rename('area')
    area_OUT.attrs["units"] = "km^2"

    # For loop to create new file
    for crop_id in cft_coord:
        area_OUT.loc[dict(cft=crop_id)] = (pct_cft.sel(cft=crop_id + 15) / 100).values * (
                    pct_crop / 100).values * land_area.values
        yield_OUT.loc[dict(cft=crop_id)] = grain4d.sel(pft=crop_id + 15)

    # Merge arrays to dataset and save
    yield_cft = xr.merge([yield_OUT, area_OUT])
    yield_cft['yield'] = yield_cft['yield'].where(yield_cft['area'] > 0)
    yield_cft.to_netcdf(savedir + '/HAYNES.{0}.nc'.format(save_name))
    return yield_cft


def Step3(yield_cft, save_name):
    savedir = '/glade/work/hayness/clm/step3'
    # (one is tropical, the other is temperate)
    crops_tot = {
        'corn': [2, 3, 60, 61],
        'cornrain': [2, 60],
        'cornirr': [3, 61],
        'rice': [46, 47],
        'ricerain': [46],
        'riceirr': [47],
        'soy': [8, 9, 62, 63],
        'soyrain': [8, 62],
        'soyirr': [9, 63],
        'springwheat': [4, 5],
        'springwheatrain': [4],
        'springwheatirr': [5],
        'cotton': [26, 27],
        'cottonrain': [26],
        'cottonirr': [27],
        'sugar': [52, 53],
        'sugarcanerain': [52],
        'sugarcaneirr': [53]
    }

    # Create empty 4D array to construct YIELD_OUT by CROP
    dims = ['crops', 'time', 'lat', 'lon']
    coords = {'time': yield_cft.time, 'crops': np.arange(0, 18, 1.0), 'lat': yield_cft.lat, 'lon': yield_cft.lon}
    yield_OUT_crop = xr.DataArray(dims=dims, coords=coords).rename('yield')
    yield_OUT_crop.attrs["units"] = "ton/ha/yr"

    # Create empty 3D array to construct AREA_OUT by CROP
    dims = ['crops', 'lat', 'lon']
    coords = {'crops': np.arange(0, 18, 1.0), 'lat': yield_cft.lat, 'lon': yield_cft.lon}
    area_OUT_crop = xr.DataArray(dims=dims, coords=coords).rename('area')
    area_OUT_crop.attrs["units"] = "km^2"

    for i, crop in enumerate(crops_tot):
        if i % 3 != 0:
            print(crop)
            IDs = crops_tot[crop]
            IDs = [id for id in IDs]
            subset = yield_cft.sel(cft=IDs)
            yields = subset['yield']
            area = subset['area']
            yields = yields.where(area > 0).sum(dim='cft', min_count=1)
            area = area.sum(dim='cft', min_count=1)
            yield_OUT_crop.loc[dict(crops=i)] = yields
            area_OUT_crop.loc[dict(crops=i)] = area

    for i, crop in enumerate(crops_tot):
        if i % 3 == 0:
            print(crop)
            yields = yield_OUT_crop.sel(crops=[i + 1, i + 2])
            area = area_OUT_crop.sel(crops=[i + 1, i + 2])
            yields = (yields * area).sum(dim='crops', min_count=1)
            area = area.sum(dim='crops', min_count=1)
            yields = yields / area
            yield_OUT_crop.loc[dict(crops=i)] = yields
            area_OUT_crop.loc[dict(crops=i)] = area

    yield_crop = xr.merge([yield_OUT_crop, area_OUT_crop])
    yield_crop.to_netcdf(savedir + '/HAYNES.{0}.nc'.format(save_name))

    return yield_crop


#################
#     STEP 1    #
#################

load_path = '/glade/work/hayness/clm/grainc'

grainc_names = ['b.e21.BWSSP534oscmip6.f09_g17.CMIP6-SSP5-3.4OS-WACCM.001.clm2.h1.GRAINC_TO_FOOD',
                'b.e21.BWSSP534oscmip6.f09_g17.CMIP6-SSP5-3.4OS-WACCM.feedback.15C.001.clm2.h1.GRAINC_TO_FOOD',
                'b.e21.BWSSP534oscmip6.f09_g17.CMIP6-SSP5-3.4OS-WACCM.feedback.20C.001.clm2.h1.GRAINC_TO_FOOD',
                'b.e21.BWSSP585cmip6.f09_g17.CMIP6-G6solar-WACCM.001.clm2.h1.GRAINC_TO_FOOD',
                'b.e21.BWSSP585cmip6.f09_g17.CMIP6-G6sulfur-WACCM.001.clm2.h1.GRAINC_TO_FOOD',
                'b.e21.BWSSP585cmip6.f09_g17.CMIP6-SSP5-8.5-WACCM.001.clm2.h1.GRAINC_TO_FOOD',
                'b.e21.BWSSP585cmip6.f09_g17.CMIP6-SSP5-8.5-WACCM.feedback.15C.001.clm2.h1.GRAINC_TO_FOOD']

years = [['2040', '2100'],
         ['2040', '2100'],
         ['2033', '2099'],
         ['2019', '2100'],
         ['2020', '2100'],
         ['2015', '2100'],
         ['2019', '2100']]

for grainc_name, year in zip(grainc_names, years):
    grainc = xr.open_mfdataset('{0}/{1}*.nc'.format(load_path, grainc_name))['GRAINC_TO_FOOD']
    start_date, end_date = year
    save_name = '{0}.{1}-{2}.nc'.format(grainc_name.replace('GRAINC_TO_FOOD', 'yield_latlon'), start_date, end_date)
    print(grainc, start_date, end_date)
    grain4d, land_area = Step1(grainc, start_date, end_date, save_name, save_file=True)

