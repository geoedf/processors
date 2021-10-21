from setuptools import setup, find_packages

setup(name='pickleghcnddata',
      version='0.1',
      description='Processor for creating a pickle file from rolling 30 and 7 day windows for various GHCND meteorological datasets',
      url='http://github.com/geoedf/processors',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['pandas'],
      zip_safe=False)
