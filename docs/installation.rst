.. highlight:: shell

============
Installation
============


Stable release
--------------

To install fairops, run this command in your terminal:

.. code-block:: console

    $ pip install fairops

This is the preferred method to install fairops, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for fairops can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/acomphealth/fairops

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/acomphealth/fairops

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ pip install -e .


.. note::
    For installation, we suggest a virtual environment like Anaconda_
    set to Python_ 3.12 like so: ``conda create -n fairops_env python=3.12``


.. _Github repo: https://github.com/acomphealth/fairops
.. _tarball: https://github.com/idekerlab/acomphealth/fairops/main
.. _Python:  https://python.org
.. _Anaconda: https://www.anaconda.com
