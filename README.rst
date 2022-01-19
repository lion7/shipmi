==========
Shell IPMI
==========

Credits
--------

This project is a fork of https://github.com/openstack/virtualbmc.
Many thanks to the OpenStack team for creating an awesome piece of software!

Overview
--------

A virtual BMC for executing shell scripts using IPMI commands.

Installation
~~~~~~~~~~~~

.. code-block:: bash

  pip install shipmi


Supported IPMI commands
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  # Power the virtual machine on, off, graceful off, NMI and reset
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power on|off|soft|diag|reset

  # Check the power status
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status

  # Set the boot device to network, hd or cdrom
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 chassis bootdev pxe|disk|cdrom

  # Get the current boot device
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 chassis bootparam get 5


How to use ShIPMI
=====================

The ShIPMI tool is a client-server system where ``shipmid`` server
does all the heavy-lifting (speaks IPMI, calls shell scripts) while ``shipmi``
client is merely a command-line tool sending commands to the server and
rendering responses to the user.

Both tools can make use of an optional configuration file, which is
looked for in the following locations (in this order):

* ``SHIPMI_CONFIG`` environment variable pointing to a file
* ``$HOME/.shipmi/daemon.conf`` file
* ``/etc/shipmi/daemon.conf`` file

If no configuration file has been found, the internal defaults apply.

You should set up your systemd to launch the ``shipmid`` server on system
start up or you can just run ``shipmid`` from command line if you do not need
the tool running persistently on the system. Once the server is up and
running, you can use the ``shipmi`` tool to configure your virtual BMCs as
if they were physical hardware servers.

The ``shipmi`` client can only communicate with ``shipmid`` server if both are running on the same host.

By this moment you should be able to have the ``ipmitool`` managing ShIPMI instances over the network.

Configuring virtual BMCs
---------------------------

Use the ``shipmi`` command-line tool to create, delete, list, start and stop virtual BMCs being managed over IPMI.

* In order to see all command options supported by the ``shipmi`` tool
  do::

    $ shipmi --help


  It's also possible to list the options from a specific command. For
  example, in order to know what can be provided as part of the ``add``
  command do::

    $ shipmi add --help


* Adding a new virtual BMC called ``node-0``::

    $ shipmi add node-0


* Adding a new virtual BMC called ``node-1`` that will listen for IPMI commands on port ``6230``::

    $ shipmi add node-1 --port 6230


.. note::

   Binding a network port number below 1025 is restricted and only users
   with privilege will be able to start a virtual BMC on those ports.


* Starting the virtual BMC called ``node-0``::

    $ shipmi start node-0


* Stopping the virtual BMC called ``node-0``::

    $ shipmi stop node-0


* Getting the list of virtual BMCs including their provider and
  IPMI network endpoints they are reachable at::

    $ shipmi list
    +--------+---------+---------+------+------------+
    | Name   |  Status | Address | Port | Provider   |
    +--------+---------+---------+------+------------+
    | node-0 | running |    ::   | 623  | proxmox-qm |
    | node-1 | running |    ::   | 6230 | proxmox-qm |
    +--------+---------+---------+------+------------+

* To view configuration information for a specific virtual BMC::

    $ shipmi show node-0
    +-----------------------+----------------+
    |        Property       |     Value      |
    +-----------------------+----------------+
    |        address        |       ::       |
    |          name         |     node-0     |
    |        password       |      ***       |
    |          port         |      623       |
    |         status        |    running     |
    |        username       |     admin      |
    |        provider       |   proxmox-qm   |
    +-----------------------+----------------+


Server simulation
-----------------

Once the virtual BMC has been created and started you can then issue IPMI commands
against the address and port of that virtual BMC. For example:

* To power on the virtual machine::

    $ ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6230 power on

* To check its power status::

    $ ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6230 power status

* To set the boot device to disk::

    $ ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6230 chassis bootdev disk

* To get the current boot device::

    $ ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6230 chassis bootparam get 5

