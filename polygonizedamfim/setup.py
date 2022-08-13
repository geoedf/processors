from setuptools import setup, find_packages

setup(name='polygonizedamfim',
      version='0.1',
      description='Processor for converting dam flood inundation maps from GeoTIFF to Shapefile',
      url='http://github.com/geoedf/polygonizedamfim',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['geopandas','shapely','xarray-spatial','rasterio','pygeos','rioxarray'],
      zip_safe=False)
