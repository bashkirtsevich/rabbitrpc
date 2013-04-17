# coding=utf-8

from distutils.core import setup


f = open('README.rst')
try:
    readme_content = f.read()
except:
    readme_content = ''
finally:
    f.close()


setup(name='rabbitrpc',
      version='0.6.0',
      platforms=('Any'),
      author='Nick Whalen',
      author_email='nickw@mindstorm-networks.net',
      url='https://github.com/nwhalen/rabbitrpc',
      download_url='https://github.com/nwhalen/rabbitrpc/tarball/master',
      description='RabbitMQ/AMQP-based RPC Client/Server Library',
      long_description=readme_content,
      packages=['rabbitrpc', 'rabbitrpc.client', 'rabbitrpc.examples', 'rabbitrpc.rabbitmq', 'rabbitrpc.server'],
      requires=['pika (>=0.9.8)'],
      provides=['rabbitrpc', 'rabbitrpc.client', 'rabbitrpc.examples', 'rabbitrpc.rabbitmq', 'rabbitrpc.server'],
      keywords='rabbitmq rpc amqp',
      license='Apache License 2.0',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2',
                   'License :: OSI Approved :: Apache Software License',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   ],
      )