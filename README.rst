paralyze
========

**sparc**, an acronym for Scientific PARameter Collection, is a Python module that provides several classes
to *create*, *edit*, *visualize*, and *serialize* many kinds of (scientific) parameter structures. In the world of
**sparc**, a parameter is a name-value pair associated with an optional physical unit. Parameters can be nested by using
the ``ParamSet`` or ``ParamGroup`` container classes. Values (and units) of parameters can also depend on other parameters
by using the ``DependentParam`` class, thereby emulating spreadsheet-like behavior. For more examples on how **sparc** can
be used, please refer to the examples_ section.

**sparc** is developed by Tobias Schruff <tobias.schruff@gmail.com>.

Dependencies
------------

**sparc** is completely written in the Python programming language. To install it, only a few dependencies have to be
satisfied. ::

- Python (>= 2.6 or >= 3.2)
- pint (>= 0.5.0)

Optionally, if you want to use the ``gui`` module, you also have to install the following dependencies ::

- PyQt5

Installation
------------

If you already have all dependencies installed, the easiest way to install **sparc** is using ``pip`` ::

    pip install sparc


.. _examples:
Examples
--------

