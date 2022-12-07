import pandas as pd
import xarray as xr


def _construct_url(ts):
    # https://thredds.met.no/thredds/dodsC/meps25epsarchive/2022/08/01/meps_det_2_5km_20220801T06Z.nc
    baseurl = "https://thredds.met.no/thredds/dodsC/meps25epsarchive"
    basefile = "meps_det_2_5km"
    url = "%s/%04d/%02d/%02d/%s_%04d%02d%02dT%02dZ.nc" % (
        baseurl,
        ts.year,
        ts.month,
        ts.day,
        basefile,
        ts.year,
        ts.month,
        ts.day,
        ts.hour,
    )
    return url


ts = pd.Timestamp("2022-12-01T00:00:00Z")
url = _construct_url(ts)
print(url)

with xr.open_dataset(url) as ds:
    latitude = ds["latitude"].data
    longitude = ds["longitude"].data
    latitude = latitude.ravel()
    longitude = longitude.ravel()
    df = pd.DataFrame(data={"longitude": longitude, "latitude": latitude})
    df.to_csv("grid.csv", index=False, header=True)
