"""Download an ERS or Envisat product from ESA according to its
product identifier.
"""

from datetime import datetime
import os
import sqlite3
from time import sleep
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
import requests
from tqdm import tqdm

from asarapi.catalog import _connect_db


BASE_URL = 'https://eo-sso-idp.eo.esa.int'
ADMIN_URL = 'https://eo-sso-idp.eo.esa.int/idp/umsso20/admin'
LOGOUT_URL = 'https://eo-sso-idp.eo.esa.int/idp/profile/Logout?execution=e3s1'


def log_in(username, password):
    """Log-in to ESA Single Sign-In service."""
    session = requests.session()
    data_dir = os.path.join(os.path.dirname(__file__))
    session.verify = os.path.join(data_dir, 'certs.pem')

    # Find login URL
    r = session.get(ADMIN_URL, allow_redirects=True)
    soup = BeautifulSoup(r.text, 'html.parser')
    for link in soup.find_all('a'):
        if 'Login' in link.getText():
            url = link.attrs['href']
    login_url = urljoin(BASE_URL, url)

    payload = {
        'cn': username,
        'password': password,
        'loginFields': 'cn@password',
        'loginMethod': 'umsso',
        'sessionTime': 'oneday',
        'idleTime': 'oneday'
    }

    # Login
    r = session.head(login_url)
    login_url = r.headers['Location']
    session.head(login_url)
    r = session.post(login_url, data=payload)

    if r.status_code != 200 or not 'logged in' in r.text:
        raise requests.exceptions.ConnectionError('Login failed.')
    
    return session


def log_out(session):
    """Close session."""
    session.get(LOGOUT_URL)
    session.close()


def _dl_url(product_id):
    """Get download URL from product id."""
    conn = _connect_db()
    c = conn.cursor()
    c.execute('SELECT url FROM products WHERE id = ?;', (product_id, ))
    url = c.fetchone()[0]
    conn.close()
    return url


def _dl_file(session, url, outdir, override=False, progressbar=False):
    """Download file from URL."""
    r = session.get(url, stream=True)
    filename = url.split('/')[-1]
    if os.path.isfile(os.path.join(outdir, filename)) and not override:
        raise FileExistsError('%s already exists. Skipping...' % filename)
    length = int(r.headers['Content-Length'])
    if progressbar:
        progress = tqdm(total=length, unit='B', unit_scale=True)
    outfile = os.path.join(outdir, filename)
    with open(outfile, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
                if progressbar:
                    progress.update(1024*1024)
    if progressbar:
        progress.close()


def request_download(session, product_id, outdir, override=False,
                     progressbar=False):
    """Request download to ESA and interpret the response."""
    product_url = _dl_url(product_id)
    r = session.get(product_url, stream=True)

    # Product is not available
    if r.status_code == 404:
        xmlroot = ET.fromstring(r.text)
        for child in xmlroot:
            if 'ResponseMessage' in child.tag:
                error_msg = child.text
        raise requests.exceptions.InvalidURL(error_msg)
    
    # Product is available, but ESA must process the order
    if r.status_code == 202:
        # Resend query to get correct "Retry-After" header value
        r = session.get(product_url, stream=True)
        retry_after = int(r.headers['Retry-After'])
        if progressbar:
            print('The order is being processed by ESA '
                'and will be ready in {} seconds.'.format(retry_after))
            progress = tqdm(total=retry_after)
        for i in range(retry_after):
            sleep(1)
            if progressbar:
                progress.update(1)
        if progressbar:
            progress.close()
        request_download(session, product_id, outdir, override=override,
                         progressbar=progressbar)
    
    # Product is directly available
    if r.status_code == 200:
        _dl_file(session, product_url, outdir, progressbar=progressbar)
