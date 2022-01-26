#!/usr/bin/env python

from distutils.core import setup

setup(name='sungrow-websocket',
      version='1.0',
      description='Sungrow Inverter Websocket API',
      author='Stefan Wallentowitz',
      author_email='stefan@wallentowitz.de',
      url='',
      packages=['sungrowws'],
      install_requires=["websockets", "requests", "terminaltables"],
      entry_points = {
            "console_scripts": ["sungrow-websocket=sungrowws:main"]
      }
)