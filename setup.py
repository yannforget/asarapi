import codecs
from os import path

from setuptools import find_packages, setup

HERE = path.abspath(path.dirname(__file__))

with codecs.open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='asarapi',
    version='0.6',
    description='Search and download ERS-1, ERS-2, and Envisat products.',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/yannforget/asarapi',
    author='Yann Forget',
    author_email='yannforget@mailbox.org',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    keywords=['earth observation', 'gis', 'remote sensing'],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'requests',
        'click',
        'pandas',
        'tqdm',
        'shapely',
        'appdirs',
        'bs4'
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points="""
        [console_scripts]
        asarapi=asarapi.cli:cli
    """,
)
