"""
Download multiple days for NWP product.

Careful, lots of stuff is hardcoded in nwpstuff.download_nwp()!
"""

import pandas as pd
import nwpstuff
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('-s', '--start', default='2019-01-01', 
                    help='First Day to Download.')
parser.add_argument('-e', '--end', default='2019-01-02', 
                    help='Last Day to Download.')
parser.add_argument('-b', '--basedir', default='/tmp/vesselai',
                    help='Base Directory for Files')
parser.add_argument('--force', action='store_true', default=False)
args = parser.parse_args()

dates = pd.date_range(start=args.start, end=args.end)
# print(dates)

for date in dates:
    date = date.strftime("%Y-%m-%d")
    print("[*] Downloading NWP Product for %s." % date)
    _ = nwpstuff.download_nwp(date, args.basedir, args.force)
