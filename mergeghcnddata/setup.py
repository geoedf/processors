from setuptools import setup, find_packages

setup(name='mergeghcnddata',
      version='0.1',
      description='Processor for merging per-station, per GHCND parameter data CSVs',
      url='http://github.com/geoedf/processors',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['pandas'],
      zip_safe=False)
