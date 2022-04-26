"""
Download a given date for NWP product.

Careful, lots of stuff is hardcoded in nwpstuff.download_nwp()!
"""

import nwpstuff
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--date', default='2019-01-01', 
                    help='Date for NWP Data')
parser.add_argument('-b', '--basedir', default='/tmp/vesselai',
                    help='Base Directory for Files')
parser.add_argument('--force', action='store_true', default=False)
parser.add_argument('-q', '--quiet', action='store_true', default=False)
args = parser.parse_args()

print("[*] Downloading NWP Product.")
_ = nwpstuff.download_nwp(args.date, args.basedir, args.force, args.quiet)
