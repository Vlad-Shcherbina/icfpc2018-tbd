with import <nixpkgs> {};
with python3Packages;

buildPythonApplication {
  name = "icfpc2018";
  src = lib.cleanSource ./.;

  nativeBuildInputs = [ cmake ];
  preConfigure = "cmake . && make";

  propagatedBuildInputs = [ flask nose psycopg2 pytest (z3.override { inherit python; }) ];
}
