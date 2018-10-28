"""Search for ERS-1, ERS-2, and ENVISAT Level-1 products through a local
SQLite dump of the ESA Online Catalogue (http://esar-ds.eo.esa.int/sxcat).
"""

import os
import sqlite3

import pandas as pd
import requests
from appdirs import user_data_dir
from tqdm import tqdm

CATALOG_URL = 'http://data.yannforget.me/asarapi/catalog.db'
DATA_DIR = user_data_dir('asarapi')


def check_catalog():
    """Check that the catalog is downloaded."""
    expected_path = os.path.join(DATA_DIR, 'catalog.db')
    return os.path.isfile(expected_path)


def download_catalog():
    """Download `catalog.db`."""
    os.makedirs(DATA_DIR, exist_ok=True)
    r = requests.get(CATALOG_URL, stream=True)
    out_path = os.path.join(DATA_DIR, 'catalog.db')
    file_size = int(r.headers['Content-Length'])
    progress = tqdm(total=file_size, unit='b', unit_scale=True)
    with open(out_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
                progress.update(1024*1024)
    progress.close()


def _check_param(value, possible):
    """Check a string parameter according to a list of possible values.
    The test is case insensitive.
    """
    if not value:
        return True
    possible = [s.lower() for s in possible]
    return value.lower() in possible


def _build_query(relation, area, start, end, platform,
                 product, orbit, polarisation, limit):
    sql = ('SELECT id, date, platform, orbit, polarisation, swath, url, '
           'AsText(geom) AS footprint '
           'FROM products '
           'WHERE {relation}(geom, GeomFromText("{area}", 4326)) '
           'AND Area(geom) < 10 '
           'AND date BETWEEN {start} AND {end} ')
    sql = sql.format(relation=relation, area=area, start=start, end=end)

    # Product type. Precision Image = IMP ; Single-Look Complex = IMS.
    if 'look' in product or 'single' in product or 'complex' in product:
        sql += 'AND SUBSTR(id, 5, 3) = "IMS" '
    else:
        sql += 'AND SUBSTR(id, 5, 3) = "IMP" '

    if platform:
        sql += 'AND platform = "{}" COLLATE NOCASE '.format(platform)
    if orbit:
        sql += 'AND orbit = "{}" COLLATE NOCASE '.format(orbit)
    if polarisation:
        sql += 'AND polarisation = "{}" COLLATE NOCASE '.format(polarisation)
    
    # Use spatial index
    sql += """AND products.ROWID IN (
        SELECT ROWID FROM SpatialIndex
        WHERE f_table_name = 'products'
        AND search_frame = GeomFromText("{}")) """.format(area)
    
    sql += 'LIMIT {};'.format(limit)

    return sql


def _connect_db():
    dbpath = os.path.join(DATA_DIR, 'catalog.db')
    conn = sqlite3.connect(dbpath)
    conn.enable_load_extension(True)
    conn.execute('SELECT load_extension("mod_spatialite");')
    return conn


def query(area, start, stop, platform=None, product='precision', orbit=None,
          polarisation=None, contains=False, limit=500):
    """Query the SQLite database.

    Parameters
    ----------
    area : str
        Area of interest in WKT.
    start : datetime
        Start search date.
    stop : datetime
        Stop search date.
    platform : str
        Platform short name [ERS, Envisat].
    product : str
        Product type [Precision, Single-Look Complex].
    orbit : str
        Orbit direction [Ascending, Descending].
    polarisation : str
        Polarisation channels [VV, HH].
    contains : bool, optional
        `area` must contains the product footprint.
    limit : int, optional
        Max. number of results. Defaults to 500.

    Returns
    -------
    products : dataframe
        Result of the query as a pandas dataframe.
    """
    # Compatibility with spatialite datatypes
    start = int(start.timestamp())
    stop = int(stop.timestamp())

    relation = 'Intersects'
    if contains:
        relation = 'Contains'

    # Check parameters
    _check_param(platform, ['ERS', 'Envisat'])
    _check_param(orbit, ['Ascending', 'Descending'])
    _check_param(polarisation, ['VV', 'VH', 'HV', 'HH'])

    sql = _build_query(relation, area, start, stop, platform, product.lower(),
                       orbit, polarisation, limit)
    conn = _connect_db()
    products = pd.read_sql_query(sql, conn, index_col='id', parse_dates=['date'])
    conn.close()

    if len(products) > limit:
        return products.iloc[:500]
    else:
        return products
