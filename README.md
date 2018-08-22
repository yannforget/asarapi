[![DOI](https://zenodo.org/badge/145747919.svg)](https://zenodo.org/badge/latestdoi/145747919)

## Description

**ASARapi** is a simple Python command-line program that allows you to search the [ESA Online Catalogue](http://esar-ds.eo.esa.int/sxcat) for SAR images produced by the [ERS-1](https://earth.esa.int/web/sppa/mission-performance/esa-missions/ers-1) (1991-2000), [ERS-2](https://earth.esa.int/web/sppa/mission-performance/esa-missions/ers-2) (1995-2011), or [Envisat](https://earth.esa.int/web/sppa/mission-performance/esa-missions/envisat) (2002-2012) satellites and to download them.

The following collections are supported:

* `ASA_IMP_1P`: Level 1 products for ENVISAT ASAR Image Mode Precision Image.
* `ASA_IMS_1P`: Level 1 products for ENVISAT ASAR Image Mode Single-Look
  Complex.
* `SAR_IMP_1P`: Level 1 products for ERS SAR Precision Image.
* `SAR_IMS_1P`: Level 1 products for ERS SAR Single-Look Complex.

## Installation

**ASARapi** can be installed using `pip`.

```sh
pip install asarapi
```

## Usage

### Sync database

**ASARapi** is designed to work with a local SQLite dump of the ESA Online Catalogue in order to speed up spatial queries. Therefore, the database must be downloaded before using the program by running the `sync` subcommand.

```bash
asarapi sync
```

The file will be stored in your user data directory, e.g. `~/.local/share/asarapi` on Linux, `/Users/<user>/Library/Application Support/asarapi` on OSX, or `C:\Users\<user>\AppData\Local\asarapi` on Windows.

Please see [`yannforget/esa-online-catalogue`](https://github.com/yannforget/esa-online-catalogue) for further details regarding the scraping of the ESA Online Catalogue.

### Search the catalog

#### Usage

```
Usage: asarapi search [OPTIONS]

  Search for ERS and Envisat products.

Options:
  --geojson PATH                  GeoJSON footprint.
  --start TEXT                    Start date (YYYY-MM-DD).
  --stop TEXT                     Stop date (YYYY-MM-DD).
  --latlon FLOAT...               Decimal lat/lon.
  --bounds FLOAT...               (max_lat, max_lon, min_lat, min_lon).
  --platform TEXT                 Platform of interest (ERS or ENVISAT, default = all)
  --product TEXT                  Product type (Precision (default) or Single-Look).
  --polarisation TEXT             Polarisation channels (default = all).
  --orbit [ascending|descending]  Orbit direction (default = all).
  --contains                      Footprint contained by input geom (default = False).
  --limit INTEGER                 Max. number of results (default = 500).
  --output PATH                   Output CSV file.
  --help                          Show this message and exit.
```

By default, `asarapi search` will output the product IDs that satisfy the query. A CSV file containing the metadata and the footprint of each scene can be generated with the `--output` option.

#### Examples

```sh
# All available products between 1995 and 1999 according to an area of interest
# defined in a GeoJSON file.
asarapi search --start 1995-01-01 --stop 1999-12-31 --geojson aoi.geojson

# All available products between 1995 and 1999 that intersect the given location
asarapi search --start 1995-01-01 --stop 1999-12-31 --latlon 16.27 -0.04

# Envisat Single-Look Complex images for a given AOI
asarapi search --start 2002-01-01 --stop 2005-01-01 --geojson aoi.geojson \
        --platform envisat --product single-look --orbit descending

# Write the result of a query in a .CSV file
asarapi search --start 1995-01-01 --stop 1999-12-31 --geojson aoi.geojson \
        --output products.csv
```

### Download a product

#### Usage

To download products, you will need [ESA SSO](https://eo-sso-idp.eo.esa.int) credentials. Register for free [here](https://eo-sso-idp.eo.esa.int/idp/umsso20/registration).

```sh
Usage: asarapi download [OPTIONS] PRODUCT

  Download an ERS or Envisat product.

Options:
  -u, --username TEXT   ESA SSO username.
  -p, --password TEXT   ESA SSO password.
  -o, --outputdir PATH  Output directory.
  --help                Show this message and exit.
```

#### Example

```sh
asarapi download -u <esa_sso_username> -p <esa_sso_password> \
        "SAR_IMP_1PNESA20030215_091621_00000015A081_00465_40900_0000"
```

## API

**ASARapi** can also be used in custom Python scripts:

```python
from datetime import datetime
from shapely.geometry import Point
from asarapi.catalog import query
from asarapi.download import log_in, log_out, request_download

username = esa_sso_username
password = esa_sso_password
output_dir = '../data'
location = Point(16.84, -0.04)

results = query(
    area=location.wkt,
    start=datetime(1999, 1, 1),
    stop=datetime(2002, 1, 1),
    orbit='ascending'
)

session = log_in(username, password)
for product_id in results.index:
    request_download(session, product_id, output_dir)
log_out(session)
```
