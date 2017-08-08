from setuptools import setup

setup(name='msutils',
      version='0.0.1',
      description='Utilities for the Morning Star newspaper',
      url='https://github.com/robjwells/ms-utils',
      author='Rob Wells',
      author_email='production@peoples-press.com',
      license='MIT',
      packages=['msutils'],
      install_requires=['paramiko >= 2.2.1,< 3'],
      zip_safe=False,
      )
