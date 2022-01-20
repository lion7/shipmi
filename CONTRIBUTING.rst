Preparation
-----------

Clone the project from GitHub::

    git clone git@github.com:lion7/shipmi.git

Install the required tools::

    apt-get install python3-pip # Change to suit your Linux distribution if necessary
    python3 -m pip install --upgrade pip build tox twine

Building
--------

Run the tests::

    python3 -m tox

Build the distribution::

    python3 -m build


Contributing
------------

Open a PR on GitHub: https://github.com/lion7/shipmi/pulls


Upload to PyPi
--------------

 Note: this step is only possible if you have the correct authorizations!

Check the distribution and upload it to the TestPyPi index::

    python3 -m twine check dist/*
    python3 -m twine upload -r testpypi dist/*

Upload to the production PyPi index::

    python3 -m twine upload -r pypi dist/*

