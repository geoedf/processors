from setuptools import setup, find_packages

setup(name='cliprasterbymask',
      version='0.2',
      description='Processor for clipping a given raster file to a mask in the form of a shapefile',
      url='http://github.com/geoedf/processors',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
