# NWP Stuff

## Introduction

This module only contains code to interact with the Norwegain Coastal Wave Forecasting System (`MyWaveWam`) products from the Norwegian Meteorological Institude.

The data is available [here](https://thredds.met.no/thredds/fou-hi/mywavewam800.html)

The most interesting bit of code is perhaps the extraction of ocean variables for a list of coordinates.

## Setup

The module is really only for local use. To make sure it builds, run

```sh
python -m build
```

To make it locally available in the current virual environment as you develop, you can do an editable install, i.e.

```sh
pip install --editable .
```

See also https://setuptools.pypa.io/en/latest/userguide/development_mode.html.

## Usage

Please refer to two downloading scripts in the root directory.

## Contact & Blame

- Volker Hoffmann <volker.hoffmann@sintef.no>

