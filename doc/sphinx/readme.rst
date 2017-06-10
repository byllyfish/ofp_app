.. _readme:

PYLIBOFP: OpenFlow App Framework
================================

Pylibofp is a Python framework for creating asyncio-based applications that control 
the network using the OpenFlow protocol. Pylibofp uses a separate *oftr* process to 
terminate OpenFlow connections and translate OpenFlow messages to JSON.

.. figure:: _static/img/ofp_app_architecture.png
    :align: center
    :alt: Architecture diagram
    
    Architecture: The oftr process translates OpenFlow to JSON.

There is no built-in OpenFlow API. You construct OpenFlow messages via YAML strings or Python dictionaries. 
Incoming OpenFlow messages are generic Python objects.  Special OpenFlow constants such as 'NO_BUFFER' appear as strings.

An OpenFlow application may be composed of multiple "app modules".  The framework includes built-in "system modules" that you can build upon.

.. (TODO) image of command line 


Requirements
------------

- Python 3.5.1 or later
- oftr command line tool


Install - Linux
---------------

::

    # Install /usr/bin/oftr dependency.
    sudo add-apt-repository ppa:byllyfish/oftr
    sudo apt-get update
    sudo apt-get install oftr

    # Create virtual environment and install pylibofp.
    python3.5 -m venv myenv
    source myenv/bin/activate
    pip install pylibofp


Demos
-----

To run the controller demo::

    python -m pylibofp.demo.l2_demo --help


.. (TODO) To run the agent simulator demo::

    python -m pylibofp.demo.agent_simulator --help

.. (TODO) To run the command line tool demo::

    python -m pylibofp.demo.ofctl --help
