=========================================
Read Sungrow inverter data from websocket
=========================================

This library is used to read real time data from Sungrow inverters with the
WiNet module that expose the websocket interface.

Known supported inverters:

- SH8.0RT (SH6.0RT and SH10.0RT likely too)

To check if your inverter is supported, simply try it out!

------------
Installation
------------

Installation is straight forward:

.. code::

    pip install sungrow-websocket

----------------------
Command line interface
----------------------

The command line interface is quite simple:

.. code::

    sungrow-websocket <host>

``<host>`` is the hostname or IP address of the inverter. Check your home router
for the inverter (maybe registers as ``espressif``).

You will then get a table with the live data:

.. code::

    
    +---------------------------------------+-----------+
    | Item                                  | Value     |
    +---------------------------------------+-----------+
    | Device Status                         | Standby   |
    | Bus Voltage                           | 16.0 V    |
    | Internal Air Temperature              | 28.6 ℃    |
    | Array Insulation Resistance           | 997 kΩ    |
    | Daily Self-consumption Rate           | 23.8 %    |
    | ...                                   | ...       |

---
API
---

Using the library is easy:

.. code:: python

    >>> from sungrow_websocket import SungrowWebsocket
    >>> host = "your-ip-or-hostname"
    >>> sg = SungrowWebsocket(host)
    >>> data = sg.get_data()

``data`` is a dict of identifiers mapping to ``InverterItem`` entries:

.. code:: python

    >>> from pprint import pprint
    >>> pprint(data)
    {'air_tem_inside_machine': InverterItem(name='I18N_COMMON_AIR_TEM_INSIDE_MACHINE', desc='Internal Air Temperature', value='28.5', unit='℃'),
     'bus_voltage': InverterItem(name='I18N_COMMON_BUS_VOLTAGE', desc='Bus Voltage', value='16.0', unit='V'),

The ``name`` entry is the internal name of the item, while ``desc`` is the clear
description. This is loaded according to the locale (``en_US`` by default) and
can be set as parameter to the class:

.. code:: python

    >>> from sungrow_websocket import SungrowWebsocket
    >>> host = "your-ip-or-hostname"
    >>> sg = SungrowWebsocket(host, locale="zh_CN")
    >>> data = sg.get_data()
    >>> from pprint import pprint
    >>> pprint(data)
    {'air_tem_inside_machine': InverterItem(name='I18N_COMMON_AIR_TEM_INSIDE_MACHINE', desc='机内空气温度', value='28.5', unit='℃'),
     'bus_voltage': InverterItem(name='I18N_COMMON_BUS_VOLTAGE', desc='母线电压', value='16.0', unit='V'),

If your locale is not supported, it will fall back to ``en_US``.