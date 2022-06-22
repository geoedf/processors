from setuptools import setup, find_packages

setup(name='MergeCSVFiles',
      version='0.2',
      description='Processor plugin for merging a directory of CSV files into a single CSV file',
      url='http://github.com/geoedf/mergecsvfiles',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['pandas'],
      zip_safe=False)
