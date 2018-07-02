# How to run

Just start it in a separate terminal and forget about it, it will live reload.

Bash:
```
export FLASK_APP=production.dashboard
export FLASK_ENV=development
flask run
```

Cmd:
```
set FLASK_APP=production.dashboard
set FLASK_ENV=development
flask run
```

PowerShell:
```
$env:FLASK_APP = "production.dashboard"
$env:FLASK_ENV = "development"
flask run
```

To be sure which python is used, instead of `flask run`
write `python3.7 -m flask run` or something.
