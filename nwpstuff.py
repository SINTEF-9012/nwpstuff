"""
Stuff to interact with NWP products from MetNo.
MEPS/AROME currently unsupported.
"""

import netCDF4 as nc
import pandas as pd
import numpy as np
import subprocess
import argparse
import pyproj
import os


def download_nwp(date, basedir, force=False):
    """
    date is YYYY-MM-DD
    basedir is the path where the NWP output will be stored
    force will re-download the file even if it exists
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


def _reproject_points(x_src, y_src, src_srs, dst_srs):
    """
    Reproject (x_src,y_src) in srs_src to (x_dst,y_dst) in srs_dst.
    x_src,y_src,x_dst,y_dst can be numpy arrays.
    - > reproject(499980.0, 9000000.0, 32622, 4326)
      > -51.0011529236 81.0608809732
    - > reproject(-51.0011529236, 81.0608809732, 32622, 4326)
      > 499980.0, 9000000.0
    """
    transformer = pyproj.Transformer.from_crs(src_srs, dst_srs)
    x_dst, y_dst = transformer.transform(x_src, y_src)
    return x_dst, y_dst


def _load_nwp_grid(fname, product='mywavewam'):
    """load NWP grid"""
    with nc.Dataset(fname) as dset:
        if product in [ 'arome', 'meps' ]:
            # projection string for the spatial reference system used
            projection_string = dset['projection_lambert'].proj4  
            # coordinates arrays
            # these are masked arrays, make sure to grab the data field
            xvec = dset['x'][:].data # 1D
            yvec = dset['y'][:].data # 1D
        elif product == 'mywavewam':
            projection_string = dset['projection_3'].proj4  
            xvec = dset['rlon'][:].data
            yvec = dset['rlat'][:].data
        # data arrays, may be masked arrays
        # usually 2D (y,x) or 3D (time,y,x)
        # don't bother with actual data arrays here.
        # we just loading the grid and some metadata
        # altitude = dset['altitude'][:].data # 2D
        # longitude = dset['longitude'][:].data # 2D
        # latitude = dset['latitude'][:].data # 2D
    return xvec, yvec, projection_string


def _coords_to_index(coord, xc):
    """
    given a coordinate and a grid, find index of the grid cell the coord is in.
    `coord` is the coordinate and `xc` the grid centerpoints.
    for example, looking for `coord = 0.32` in `xc = [ 0.1, 0.2, 0.3, 0.4]`
    will yield and `xidx = 2`. we assume that xc is evenly spaced.
    """
    dx = np.diff(xc)[0] # assume even spacing
    xl = xc - dx/2.0    # left edges
    xr = xc + dx/2.0    # right edges
    # https://stackoverflow.com/q/36941294
    #xidx = xc[np.logical_and(coord>xl, coord<xr)][0]
    xidx, = np.where(np.logical_and(coord>xl, coord<xr))[0]
    return xidx


def get_nwp_at_latlon_ts(fname_nwp, 
                         lon_req=[10.5,10.6],
                         lat_req=[59.5,59.6],
                         ts_req='2019-01-01T000000Z',
                         product='mywavewam'):
    """
    fname_nwp is the path to the NWP product
    lon_req, lat_req are in WGS84 (EPSG:4326)
    ts is ISO 8601 (e.g., 2019-09-06T134500Z is valid)
    product can be `arome`, `meps`, or `mywavewam`
    @todo: arome/meps
    """
    
    # load coordinates available in NWP grid
    xvec, yvec, projection_string = _load_nwp_grid(fname_nwp, 
                                                   product=product)
    
    # reproject requested coordinates (WGS84/EPSG4326) into nwp grid
    xcoords_req = lon_req
    ycoords_req = lat_req
    xcoords, ycoords = \
        _reproject_points(xcoords_req, ycoords_req, \
                          "epsg:4326", \
                          projection_string)
    
    # compute corresponding index in NWP grid
    xidx = [ _coords_to_index(xcoords[kk], xvec) for kk in range(len(xcoords)) ]
    yidx = [ _coords_to_index(ycoords[kk], yvec) for kk in range(len(ycoords)) ]
    
    # load nwp timestamp and find time index
    with nc.Dataset(fname_nwp) as dset:
        ts = pd.to_datetime(dset['time'][:], unit='s', origin='unix', utc=True)
        tidx = np.argwhere(ts==pd.to_datetime(ts_req))[0][0]
       
    # recover NWP data
    with nc.Dataset(fname_nwp) as dset:
        # coords for sanity checking
        lon_out = []
        lat_out = []
        # nwp variables
        hs_sea = []
        for kk in range(len(xidx)):
            # coords
            lon_out.append(dset['lon'][yidx[kk],xidx[kk]].data)
            lat_out.append(dset['lat'][yidx[kk],xidx[kk]].data)
            # nwp
            hs_sea.append(dset['hs_sea'][tidx,yidx[kk],xidx[kk]].data)

    # make dataframe
    nwp_dict = { 'ts': pd.to_datetime(ts_req, utc=True), 
                 'lon_out': lon_out, 'lat_out': lat_out,
                 'hs_sea': hs_sea }
    df = pd.DataFrame(data=nwp_dict)

    # return
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    # group.add_argument('--arome', action='store_true', help='AROME NWP')
    # group.add_argument('--meps', action='store_true', help='MEPS NWP')
    group.add_argument('--mywavewam', action='store_true', help='MyWaveWam')
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
                              product='mywavewam')

    print("[*] Output Dataframe Follows")
    print(df)
