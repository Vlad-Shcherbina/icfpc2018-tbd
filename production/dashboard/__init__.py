import flask

from production import db


app = flask.Flask(__name__)


@app.before_first_request
def init():
    import logging
    for logger in logging.getLogger('werkzeug'), app.logger:
        hs = logger.handlers[:]
        for h in hs:
            logger.removeHandler(h)

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')


_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = db.get_conn()
    return _conn


@app.route('/')
def hello():
    return flask.render_template_string('''\
    {% extends "base.html" %}
    {% block body %}
    Hello, world!
    {% endblock %}
    ''')


# circular imports in this package organization are justified by
# http://flask.pocoo.org/docs/1.0/patterns/packages/
import production.dashboard.invocation_views
