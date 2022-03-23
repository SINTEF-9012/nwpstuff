"""
Stuff to interact with `MyWaveWam` NWP products from MetNo.
"""

import netCDF4 as nc
import pandas as pd
import numpy as np
import subprocess
import pyresample
import argparse
import os


def download_nwp(date, basedir, force=False):
    """
    date is YYYY-MM-DD
    basedir is the path where the NWP output will be stored
    force will re-download the file even if it exists

    cf. https://thredds.met.no/thredds/fou-hi/mywavewam800.html
    we use MyWaveWam800m Skagerrak Hourly Aggregation
    then click `NetcdfSubset`
    """
    date = date.split('-')
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    url = "https://thredds.met.no/thredds/ncss/fou-hi/mywavewam800s_be?"
    url += "var=latitude&"
    url += "var=longitude&"
    url += "var=Pdir&"
    url += "var=dd&"
    url += "var=ds&"
    url += "var=ds_sea&"
    url += "var=ds_swell&"
    url += "var=ff&"
    url += "var=hs&"
    url += "var=hs_sea&"
    url += "var=hs_swell&"
    url += "var=kurtosis&"
    url += "var=mHs&"
    url += "var=msqs&"
    url += "var=mwp&"
    url += "var=thq&"
    url += "var=thq_sea&"
    url += "var=thq_swell&"
    url += "var=tp&"
    url += "var=tp_sea&"
    url += "var=tp_swell&"
    url += "north=60.3968&"
    url += "west=10&"
    url += "east=11.8328&"
    url += "south=59&"
    url += "disableProjSubset=on&"
    url += "horizStride=1&"
    url += "time_start=%04d-%02d-%02dT00:00:00Z&" % (year, month, day)
    url += "time_end=%04d-%02d-%02dT23:00:00Z&" % (year, month, day)
    url += "timeStride=1&"
    url += "addLatLon=true"
    fname = "%s/mywavewam800s_be_%04d-%02d-%02d.nc" % (basedir, 
                                                       year, month, day)
    if os.path.exists(fname):
        print("[!] %s Exists." % fname)
        if force == True:
            print('[!] Forcing Download.')
            subprocess.run(['wget', '-O', fname, url])
        else:
            print('[!] Skipping Download.')
    else:
        subprocess.run(['wget', '-O', fname, url])

    return fname


def _load_nwp_grid(fname):
    """load NWP grid"""
    with nc.Dataset(fname) as dset:
        # data arrays, may be masked arrays
        # usually 2D (y,x) or 3D (time,y,x)
        # don't bother with actual data arrays here.
        # we just loading the grid and some metadata
        # altitude = dset['altitude'][:].data # 2D
        longitude = dset['longitude'][:].data # 2D
        latitude = dset['latitude'][:].data # 2D
    return longitude, latitude


def get_nwp_at_latlon_ts(fname_nwp, 
                         lon_req=[10.5,10.6],
                         lat_req=[59.5,59.6],
                         ts_req='2019-01-01T000000Z',
                         as_dataframe=True):
    """
    fname_nwp is the path to the NWP product
    lon_req, lat_req are in WGS84 (EPSG:4326)
    ts is ISO 8601 (e.g., 2019-09-06T134500Z is valid)
    @todo: arome/meps
    """
    
    # use a kdtree to find the nearest neighbours to the requested lon,lat
    # on the lat,lon grid included in the nwp product
    # cf. https://stackoverflow.com/a/40044540

    # load coordinates available in NWP grid
    lon_grid, lat_grid = _load_nwp_grid(fname_nwp)

    grid = pyresample.geometry.GridDefinition(lons=lon_grid, lats=lat_grid)
    swath = pyresample.geometry.SwathDefinition(lons=lon_req, lats=lat_req)

    # nearest neighbours (wrt great circle distance) in the grid
    _, _, index_array, distance_array = \
        pyresample.kd_tree.get_neighbour_info(source_geo_def=grid,
                                              target_geo_def=swath,
                                              radius_of_influence=50000,
                                              neighbours=1)

    # unflatten the indices
    index_array_2d = np.unravel_index(index_array, grid.shape)
    # index_array_lon = index_array_2d[0]
    # index_array_lat = index_array_2d[1]

    # load nwp timestamp and find time index
    with nc.Dataset(fname_nwp) as dset:
        ts = pd.to_datetime(dset['time'][:], unit='s', origin='unix', utc=True)
        tidx = np.argwhere(ts==pd.to_datetime(ts_req))[0][0]

    # recover NWP data
    with nc.Dataset(fname_nwp) as dset:
        # coords for sanity checking
        lon_out = np.ravel(dset['longitude'][:])[index_array]
        lat_out = np.ravel(dset['latitude'][:])[index_array]
        # nwp variables
        hs_sea = np.ravel(dset['hs_sea'][tidx,:])[index_array]

    # make dataframe
    nwp_dict = { 'ts': pd.to_datetime(ts_req, utc=True), 
                 'lon_out': lon_out, 'lat_out': lat_out,
                 'hs_sea': hs_sea }

    if as_dataframe == True:
        out = pd.DataFrame(data=nwp_dict)
    else:
        out = nwp_dict
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--date', default='2019-01-01', 
                        help='Date for NWP Data')
    parser.add_argument('-b', '--basedir', default='/tmp',
                        help='Base Directory for Files')
    parser.add_argument('-c', '--coords', default='10.5,59.5',
                        help='Lon,Lat of Target Coordinates (EPSG4326/WSG84')
    parser.add_argument('--force', action='store_true', default=False)
    args = parser.parse_args()
    print(args)

    print("[*] Downloading NWP Product.")
    fname_nwp = download_nwp(args.date, args.basedir, args.force)

    print("[*] Extracting NWP at Target Coordinates")
    lon_req = float(args.coords.split(',')[0])
    lat_req = float(args.coords.split(',')[1])
    df = get_nwp_at_latlon_ts(fname_nwp, 
                              lon_req=[lon_req],
                              lat_req=[lat_req],
                              ts_req="%sT000000Z" % args.date,
                              as_dataframe=True)

    print("[*] Output Dataframe Follows")
    print(df)
