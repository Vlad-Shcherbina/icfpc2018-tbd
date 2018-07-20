with import <nixpkgs> {};
with python37Packages;

stdenv.mkDerivation {
  name = "icfpc2018-tbd";

  buildInputs = [
    python
    virtualenv
    pip
    postgresql
    nodejs
  ];

  shellHook = ''
    export SOURCE_DATE_EPOCH=$(date +%s)
    virtualenv --no-setuptools virtualenv

    export PATH=$PWD/virtualenv/bin:$PATH
    pip install -r requirements.txt
  '';
}
