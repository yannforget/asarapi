"""Command-line interface."""

import json
import os
from datetime import datetime

import click
from shapely.geometry import Point, Polygon, shape

from asarapi.catalog import query, check_catalog, download_catalog
from asarapi.download import log_in, log_out, request_download


def latlon_to_wkt(lat, lon):
    return Point(lon, lat).wkt


def bounds_to_wkt(max_lat, max_lon, min_lat, min_lon):
    return Polygon([(min_lon, min_lat), (min_lon, max_lat),
                    (max_lon, max_lat), (max_lon, min_lat),
                    (min_lon, min_lat)]).wkt


def geojson_to_wkt(file_path):
    with open(file_path) as f:
        geojson = json.load(f)
    if 'geometry' in geojson:
        geom = geojson['geometry']
    else:
        geom = geojson['features'][0]['geometry']
    return shape(geom).wkt


@click.group()
def cli():
    pass


@click.command()
@click.option('--overwrite', default=False)
def sync(overwrite):
    """Download ESA catalogue."""
    if not check_catalog() or overwrite:
        download_catalog()
    else:
        click.echo('Database already downloaded.')


@click.command()
@click.option('--geojson', type=click.Path(), default=None,
              help='GeoJSON footprint.')
@click.option('--start', type=click.STRING, help='Start date (YYYY-MM-DD).')
@click.option('--stop', type=click.STRING, help='Stop date (YYYY-MM-DD).')
@click.option('--latlon', nargs=2, type=float, default=None,
              help='Decimal lat/lon.')
@click.option('--bounds', nargs=4, type=float, default=None,
              help='(max_lat, max_lon, min_lat, min_lon).')
@click.option('--platform', type=click.STRING,
              help='Platform of interest (ERS or ENVISAT).')
@click.option('--product', type=click.STRING, default='precision',
              help='Product type (`Precision` or `Single-Look`).')
@click.option('--polarisation', type=click.STRING, default=None,
              help='Polarisation channels.')
@click.option('--orbit', type=click.Choice(['ascending', 'descending']),
              default=None, help='Orbit direction.')
@click.option('--contains', is_flag=True, 
              help='Footprint contained by input geom.')
@click.option('--limit', type=click.INT, default=500,
              help='Max. number of results.')
@click.option('--output', type=click.Path(), default=None,
              help='Output CSV file.')
def search(geojson, start, stop, latlon, bounds, platform, product,
           polarisation, orbit, contains, limit, output):
    """Search for ERS and Envisat products."""
    # Get area of interest in WKT format
    if geojson:
        area = geojson_to_wkt(geojson)
    elif latlon:
        area = latlon_to_wkt(*latlon)
    elif bounds:
        area = bounds_to_wkt(*bounds)
    else:
        raise click.BadOptionUsage(
            'A location must be providied with one of the following '
            'parameters : --latlon, --bounds or --geojson.')

    # Parse dates
    start = datetime.strptime(start, '%Y-%m-%d')
    stop = datetime.strptime(stop, '%Y-%m-%d')

    results = query(
        area=area, start=start, stop=stop, platform=platform, product=product,
        orbit=orbit, polarisation=polarisation, contains=contains, limit=limit)

    if output:
        results.to_csv(output)
    else:
        for pid in results.index:
            click.echo(pid)


@click.command()
@click.option('-u', '--username', type=click.STRING, help='ESA SSO username.')
@click.option('-p', '--password', type=click.STRING, help='ESA SSO password.')
@click.option('-o', '--outputdir', type=click.Path(exists=True),
              default=os.curdir, help='Output directory.')
@click.argument('product', type=click.STRING)
def download(product, username, password, outputdir):
    """Download an ERS or Envisat product."""
    if not username or not password:
        raise click.exceptions.BadOptionUsage(
            'ESA SSO credentials are required.')
    session = log_in(username, password)
    request_download(session, product, outputdir)
    log_out(session)


cli.add_command(sync)
cli.add_command(search)
cli.add_command(download)


if __name__ == '__main__':
    cli()
