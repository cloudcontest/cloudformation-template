from setuptools import setup

setup(name='dj_cfn_generator',
      version='0.1',
      description='Cloudformation generator for DOMjudge',
      url='http://github.com/cloudcontest/dj_cfn_generator',
      author='Keith Johnson',
      author_email='kj@ubergeek42.com',
      license='MIT',
      packages=['dj_cfn_generator'],
      scripts=['bin/dj_cfn_generator'],
      install_requires=[
          'troposphere',
          'boto3',
          'docopt',
          'awacs'
      ],
      zip_safe=True)
