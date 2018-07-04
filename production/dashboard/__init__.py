import datetime

import flask

from production import db


app = flask.Flask(__name__)


@app.before_first_request
def init():
    import logging
    for logger in logging.getLogger('werkzeug'), app.logger:
        for h in logger.handlers[:]:
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


@app.template_filter('linkify')
def linkify(url):
    return flask.Markup(flask.render_template_string(
        '<a href="{{ url }}">{{ url }}</a>',
        url=url))


@app.template_filter('render_timestamp')
def render_timestamp(ts, fmt='%m-%d %H:%M:%S'):
    return flask.Markup(
        datetime.datetime.fromtimestamp(ts).strftime(fmt))


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
import production.dashboard.cars_and_fuels_views
