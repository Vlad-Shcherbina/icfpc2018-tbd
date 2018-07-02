import flask
import jinja2


app = flask.Flask(__name__)


@app.route('/')
def hello():
    return flask.render_template_string('''\
    {% extends "base.html" %}
    {% block body %}
    Hello, world!
    {% endblock %}
    ''')
