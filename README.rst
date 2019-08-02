Glue-Ginga
==========

|Build Status|

glue-ginga is a plugin viewer for the Glue viewer that uses the Ginga
viewer widget for viewing 2D images. The Ginga widget provides an
alternative viewer with many customizable features and allows Ginga
users to use a familiar interface.

In addition, it also has Glue global plugin for Ginga reference viewer,
which can be loaded as follows::

    ginga --modules=glue\_ginga.plugins.Glue

This is not compatible with Python 2.

Features
--------

-  Use the Ginga viewer widget in Glue
-  Read your custom Ginga key/mouse bindings
-  Use the Glue plugin in Ginga to transfer data between Ginga reference
   viewer and Glue viewer

Installation
------------

Installing from source::

    python setup.py install

Installing with ``pip``::

    pip install git+https://github.com/ejeschke/glue-ginga

Support
-------

Please `open an
issue <https://github.com/ejeschke/glue-ginga/issues?state=open>`__.

License
-------

Glue is licensed under the `BSD
License <https://github.com/ejeschke/glue-ginga/blob/master/LICENSE>`__

.. |Build Status| image:: https://travis-ci.org/ejeschke/glue-ginga.svg?branch=master
   :target: https://travis-ci.org/ejeschke/glue-ginga
