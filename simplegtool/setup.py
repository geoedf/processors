from setuptools import setup, find_packages

setup(name='simplegtool',
      version='0.2',
      description='Processor for converting Shapefiles to GeoJSON format',
      url='http://github.com/geoedf/simplegtool',
      author='Jungha Woo',
      author_email='jungha.woo@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['geopandas'],
      zip_safe=False)
