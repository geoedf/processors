from setuptools import setup, find_packages

setup(name='extractinundationcensustracts',
      version='0.1',
      description='Processor for determining Census tracts that fall within inundation zone of given dam inundation map',
      url='http://github.com/geoedf/extractinundationcensustracts',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['xarray','pandas','geopandas','pygeos','shapely','xarray-spatial','requests','qinfer'],
      zip_safe=False)
