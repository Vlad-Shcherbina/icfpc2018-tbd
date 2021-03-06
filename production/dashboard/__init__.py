import datetime
import html

import flask
import jinja2

from production import db
from production.dashboard.flask_utils import memoized_render_template_string


app = flask.Flask(__name__)
app.jinja_env.undefined = jinja2.StrictUndefined


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
    return flask.Markup(f'<a href="{html.escape(url)}">{url}</a>')


@app.template_filter('render_timestamp')
def render_timestamp(ts, fmt='%m-%d %H:%M:%S'):
    return flask.Markup(
        datetime.datetime.fromtimestamp(ts).strftime(fmt))


@app.route('/')
def hello():
    return memoized_render_template_string('''\
    {% extends "base.html" %}
    {% block body %}
    Hello, world!
    {% endblock %}
    ''')


# circular imports in this package organization are justified by
# http://flask.pocoo.org/docs/1.0/patterns/packages/
import production.dashboard.invocation_views
import production.dashboard.cars_and_fuels_views
import production.dashboard.models_and_traces_views
