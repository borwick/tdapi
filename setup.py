from setuptools import setup

setup(name='tdapi',
      version='0.1',
      description='TeamDynamix API',
      url='http://github.com/borwick/tdapi',
      author='John Borwick',
      author_email='john_borwick@pobox.com',
      license='MIT',
      packages=['tdapi'],
      install_requires=[
          'requests',
          'requests-cache',
          'Django',
          ],
      zip_safe=False)
