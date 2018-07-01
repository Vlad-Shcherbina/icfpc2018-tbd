## Setup

CPython 3.7.0 (the latest stable release).

Virtualenv is optional.

`pip3 install -r requirements.txt`

Copy `git_hooks/pre-push` to `.git/hooks/`.

On Windows, you'll need C++ compiler. Install Visual Studio 2015 Community or Express edition _or_ Visual C++ Build Tools 2015. Visual Studio 2017 wouldn't suffice, you'd still need 2015 Build Tools.


## Running stuff

Root of this repository should be in `PYTHONPATH`, because we use absolute imports (`from production import utils`). There are several ways to achieve that:
  - add project path to the environment variable `PYTHONPATH`
  - create the file `<python installation or venv>/lib/python3.7/site-packages/tbd.pth` whose content is a single line `/path/to/icfpc2017-tbd`
  - configure your favorite IDE appropriately
  - use `python3 -m production.some_script` instead of `python3 production/some_script.py`
