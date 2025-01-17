===============
For Developers
===============

This section provides various hints for developers intending
to contribute towards the HermesPy code base.

Unit Testing
-------------

In order to minimize the chance of code-regressions with new contributions,
HermesPy implements various automated code testing routines.
New contributions are required to pass existing tests as well as provide
tests for additional features introduced with the contribution.

In order to launch unit tests locally,

.. code-block:: bash

    python -m unittest discover tests/unit_tests

can be executed from the project's root directory.

Documentation
--------------

The documentation is generated by `Sphinx <https://www.sphinx-doc.org/>`_.
It requires some additional dependencies which may be installed from PyPi via

.. code-block:: bash

   pip install -r requirements_doc.txt

The documentation source files are located under `/docssource/`, however,
most API information should be directly inserted into the source code files and inserted
by the `autodocs <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_
extension.
A reference example can be found in `/hermespy/simulation/rf_chain/power_amplifier.py`.
See :doc:`api/simulation.rf_chain.power_amplifier` for the rendered results.

HermesPy provides a setuptools extension to build the documentation,
which can be used by executing

.. code-block:: bash

   python -m setup build_sphinx

within the root directory.
This results in the rendering of a html-based documentation website,
located under `documentation/html`.
In order to view it locally, open `index.html` within a web-browser.