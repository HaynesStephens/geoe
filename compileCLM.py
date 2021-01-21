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
import xarray as xr
import numpy as np
import pandas as pd

# Step 1
filedir = '/glade/work/hayness/g6'
filename = filedir + '/b.e21.BWSSP245cmip6.f09_g17.CMIP6-SSP2-4.5-WACCM.001.clm2.h1.GRAINC_TO_FOOD.201501-206412.nc'
ds = xr.open_dataset(filename)
grain = ds.GRAINC_TO_FOOD
pfts1d_ixy = ds.pfts1d_ixy
pfts1d_jxy = ds.pfts1d_jxy
pfts1d_wtgcell = ds.pfts1d_wtgcell
area = ds.area
landfrac = ds.landfrac
landarea = area * landfrac

grainAnn = grain.resample(time='1M').mean() * ((60*60*24*30*0.85*10)/(1000*0.45))
grainAnn.attrs["units"] = "ton/ha/yr"
