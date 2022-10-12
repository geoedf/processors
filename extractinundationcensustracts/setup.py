from setuptools import setup, find_packages

setup(name='extractinundationcensustracts',
      version='0.1',
      description='Processor for determining Census tracts that fall within inundation zone of given dam inundation map',
      url='http://github.com/geoedf/extractinundationcensustracts',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['xarray','pandas','geopandas','pygeos','shapely','xarray-spatial','requests'],
      data_files=[('data',['data/HydroRIVERS_v10_na.shp','data/HydroRIVERS_v10_na.shx','data/HydroRIVERS_v10_na.dbf','data/HydroRIVERS_v10_na.prj','data/HydroRIVERS_v10_na.sbn','data/HydroRIVERS_v10_na.sbx','data/census_tract_from_api.geojson'])],
      zip_safe=False)
