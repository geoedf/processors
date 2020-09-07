from setuptools import setup, find_packages

setup(name='simpledataclean',
      version='0.1',
      description='Processor for aggregating CSV files downloaded from FAOSTAT database',
      url='http://github.com/geoedf/simpledataclean',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      scripts=['bin/01_data_clean.r'],
      data_files=[('data',['data/reg_map.csv','data/reg_sets.csv','data/crop_sets.csv','data/livestock_sets.csv'])],
      include_package_data=True,
      zip_safe=False)
