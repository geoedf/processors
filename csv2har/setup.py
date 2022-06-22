from setuptools import setup, find_packages

setup(name='csv2har',
      version='0.2',
      description='Processor for converting a SIMPLE csv file into a HAR file',
      url='http://github.com/geoedf/csv2har',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
