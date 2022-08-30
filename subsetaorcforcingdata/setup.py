from setuptools import setup, find_packages

setup(name='subsetforcingdata',
      version='0.1',
      description='Processor for subsetting AORC forcing data for given HUC region and date range',
      url='http://github.com/geoedf/subsetaorcforcingdata',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['numpy','pandas','joblib','xarray','netCDF4'],
      #data_files=[('data',['data/huc12.shp','data/huc12.dbf','data/huc12.prj','data/huc12.shx'])],
      zip_safe=False)
