## Setup

CPython 3.7.0 (the latest stable release).

Virtualenv is optional.

`pip3 install -r requirements.txt`

Copy `git_hooks/pre-push` to `.git/hooks/`.


## Running stuff

Root of this repository should be in `PYTHONPATH`, because we use absolute imports (`from production import utils`). There are several ways to achieve that:
  - add project path to the environment variable `PYTHONPATH`
  - create the file `<python installation or venv>/lib/python3.7/site-packages/tbd.pth` whose content is a single line `/path/to/icfpc2018-tbd`
  - configure your favorite IDE appropriately
  - use `python3 -m production.some_script` instead of `python3 production/some_script.py`


## Testing stuff

```
cd icfpc2018-tbd/
python3 -m production.test_all

# or simply
cd icfpc2018-tbd/
pytest
```


## Random notes

### Windows

You'll need C++ compiler to build C++ extensions.
Install Visual Studio 2015 Community or Express edition _or_ Visual C++ Build Tools 2015.
Visual Studio 2017 wouldn't suffice, you'd still need 2015 Build Tools.

Most Python packages could be installed simply with `pip3 install whatever_package` nowadays,
but sometimes it does not work (e.g. for `psycopg2`).
In such cases, download the package from https://www.lfd.uci.edu/~gohlke/pythonlibs/
and install it manually (`pip install whatever_package.wheel`).

### WSL or Ubuntu 16.04 (Xenial)

Python:

```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.7
```

Then use `python3.7` to invoke Python,
`python3.7 -m pip` to invoke `pip`,
`python3.7 -m pytest` to invoke `pytest`,
you get the idea.

GCC:

```
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt-get update
sudo apt-get install g++-8
```

Then set environment variable `CC` to `g++-8`.