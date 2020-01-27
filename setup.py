from distutils.core import setup


with open('README.md') as f:
    long_description = f.read()


setup(
    # Application name:
    name="Power Places Scraper",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Powerplace",
    author_email="developers@powerplace.io",

    # Packages
    packages=["power_places_scraper"],

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="https://www.powerplace.io//",

    description="Scraper to retrieve places from third party sources.",

    long_description=long_description,
    long_description_content_type='text/markdown',

    entry_points={
        'console_scripts': ['power_places_scraper=power_places_scraper.cli:main'],
    },

    # Dependent packages (distributions)
    install_requires=[
        "geojson", "overpy", "PySocks", "tqdm", "requests"
    ],
)
