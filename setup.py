# coding=utf-8

from distutils.core import setup


f = open('README.rst')
try:
    readme_content = f.read()
except:
    readme_content = ''
finally:
    f.close()


f = open('requirements.txt')
try:
    requirements = f.read().splitlines()
except:
    requirements = []
finally:
    f.close()

setup(name='rabbitrpc',
      version='0.5.1',
      platforms=('Any'),
      author='Nick Whalen',
      author_email='nickw@mindstorm-networks.net',
      url='https://github.com/nwhalen/rabbitrpc',
      download_url='https://github.com/nwhalen/rabbitrpc/tarball/master',
      description='RabbitMQ/AMQP-based RPC Client/Server Library',
      long_description=readme_content,
      packages=['rabbitrpc'],
      requires=['pika (>=0.9.8)'],
      provides=['rabbitrpcclient', 'rabbitrpcserver'],
      keywords='rabbitmq rpc amqp',
      license='Apache License 2.0',
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2',
                   'License :: OSI Approved :: Apache Software License',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   ],
      )