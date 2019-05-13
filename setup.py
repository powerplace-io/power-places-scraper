from distutils.core import setup


with open('README.md') as f:
    long_description = f.read()


setup(
    # Application name:
    name="Places Scraper",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Powerplace",
    author_email="developers@powerplace.io",

    # Packages
    packages=["places_scraper"],

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="https://www.powerplace.io//",

    description="Scraper to scrape places from third party sources.",

    long_description=long_description,
    long_description_content_type='text/markdown',

    entry_points = {
        'console_scripts': ['places_scraper=places_scraper.cli:main'],
    },

    # Dependent packages (distributions)
    install_requires=[
        "pyproj", "geojson", "Jinja2", "matplotlib", "numpy", "overpy",
        "pandas", "PySocks", "ruamel.yaml", "seaborn", "tqdm"
    ],
)
