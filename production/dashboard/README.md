# How to run

Just start it in a separate terminal and forget about it, it will live reload.

Bash:
```
cd icfpc2018-tbd/
export FLASK_APP=production.dashboard
export FLASK_ENV=development
flask run
```

Cmd:
```
cd icfpc2018-tbd/
set FLASK_APP=production.dashboard
set FLASK_ENV=development
flask run
```

PowerShell:
```
cd icfpc2018-tbd/
$env:FLASK_APP = "production.dashboard"
$env:FLASK_ENV = "development"
flask run
```

To be sure which python is used, instead of `flask run`
write `python3.7 -m flask run` or something.
