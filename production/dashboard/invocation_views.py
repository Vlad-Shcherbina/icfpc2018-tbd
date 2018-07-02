import json

import flask

from production.dashboard import app, get_conn


@app.template_filter('json_dump')
def json_dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False)


@app.template_filter('render_invocation')
def render_invocation(inv, id):
    argv = ' '.join(inv['argv'])
    version = inv['version']
    return flask.Markup(flask.render_template_string('''\
    [<a href="{{ url_for('view_invocation', id=id) }}">
        {{ url_for('view_invocation', id=id) -}}
    </a>
    <b>{{ argv }}</b>
    <a href="https://github.com/Vlad-Shcherbina/icfpc2018-tbd/commit/{{
        version['commit'] }}">
        {{ version['commit'][:8] -}}
    </a>
    (#{{ version['commit_number'] }})
    {% if version['diff_stat'] %}
        <u><span title="{{ version['diff_stat'] }}">dirty</span></u>
    {% endif %}
    by <b>{{ inv['user'] }}</b>]
    ''', **locals()))


@app.route('/invs')
def list_invocations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, data FROM invocations ORDER BY id DESC')

    return flask.render_template_string(LIST_INVOCATIONS_TEMPLATE, **locals())

LIST_INVOCATIONS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All invocations</h3>
<table>
{% for id, inv in cur %}
    {% set version = inv['version'] %}
    <tr>
        <td>
            {{ inv | render_invocation(id) }}
        </td>
    </tr>
{% endfor %}
</table>
{% endblock %}
'''


@app.route('/inv/<int:id>')
def view_invocation(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT data FROM invocations WHERE id=%s', [id])
    [inv] = cur.fetchone()

    return flask.render_template_string(VIEW_INVOCATION_TEMPLATE, **locals())

VIEW_INVOCATION_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Invocation info</h3>
{{ inv | render_invocation(id) }}
<pre>{{ inv | json_dump }}</pre>
{% endblock %}
'''
