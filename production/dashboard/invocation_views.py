import json
from collections import defaultdict

import flask

from production.dashboard import app, get_conn


@app.template_filter('json_dump')
def json_dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False)


@app.template_filter('render_version')
def render_version(version):
    return flask.Markup(flask.render_template_string('''\
    <a href="https://github.com/Vlad-Shcherbina/icfpc2018-tbd/commit/{{
        version['commit'] }}">
        {{ version['commit'][:8] -}}
    </a>
    (#{{ version['commit_number'] }})
    {% if version['diff_stat'] %}
        <u><span title="{{ version['diff_stat'] }}">dirty</span></u>
    {% endif %}
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
    <tr>
        <th></th>
        <th>Command</th>
        <th>Version</th>
        <th>User</th>
        <th>Start time</th>
        <th>Last update time</th>
    </tr>
{% for id, inv in cur %}
    <tr>
        <td>{{ url_for('view_invocation', id=id) | linkify }}</td>
        <td>{{ inv['argv'] | join(' ') }}</td>
        <td>{{ inv['version'] | render_version }}</td>
        <td>{{ inv['user'] }}</td>
        <td>{{ inv['start_time'] | render_timestamp }}</td>
        <td>
            {% if inv['last_update_time'] > inv['start_time'] + 0.5  %}
                {{ inv['last_update_time'] | render_timestamp }}
            {% else %}
                same
            {% endif %}
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

    cur.execute('''
        SELECT
            problems.id, traces.energy
        FROM problems
        LEFT OUTER JOIN traces ON traces.problem_id = problems.id
    ''')
    best_by_problem = defaultdict(lambda: float('+inf'))
    for [problem_id, energy] in cur:
        if energy is not None:
            best_by_problem[problem_id] = min(best_by_problem[problem_id], energy)

    cur.execute('''
        SELECT
            id, status, energy, problem_id, scent, timestamp
        FROM traces
        WHERE invocation_id = %s
    ''', [id])
    traces = cur.fetchall()

    cur.execute(
        'SELECT id, name, timestamp FROM cars WHERE invocation_id=%s ORDER BY id DESC',
        [id])
    cars = cur.fetchall()

    cur.execute(
        'SELECT id, car_id, score, timestamp '
        'FROM fuels WHERE invocation_id = %s '
        'ORDER BY id DESC',
        [id])
    fuels = cur.fetchall()

    cur.execute(
        'SELECT id, fuel_id, data IS NOT NULL, timestamp '
        'FROM fuel_submissions WHERE invocation_id = %s '
        'ORDER BY id DESC',
        [id])
    fuel_submissions = cur.fetchall()

    return flask.render_template_string(VIEW_INVOCATION_TEMPLATE, **locals())

VIEW_INVOCATION_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Invocation info</h3>

Command: <b>{{ inv['argv'] | join(' ') }}</b> <br>
Version: {{ inv['version'] | render_version }} <br>
Run by: <b>{{ inv['user'] }}</b> <br>
Start time: {{ inv['start_time'] | render_timestamp }} <br>
Last update time: {{ inv['last_update_time'] | render_timestamp }} <br>
<pre>{{ inv | json_dump }}</pre>

{% if traces %}
<h4>Traces</h4>
<table>
{% for id, status, energy, problem_id, scent, timestamp in traces %}
    <tr>
        <td>{{ url_for('view_problem', id=problem_id) | linkify}}</td>
        <td>{{ url_for('view_trace', id=id) | linkify}}</td>
        <td>{{ status }}</td>
        <td>
            {% if energy == best_by_problem[problem_id] == energy %}
                <b>{{ energy }}</b>
            {% else %}
                {{ energy }}
            {% endif %}
        </td>
        <td>{{ scent }}</td>
        <td>{{ timestamp | render_timestamp }}</td>
    </tr>
{% endfor %}
</table>
{% endif %}

{% if cars %}
<h4>Cars</h4>
<table>
{% for id, name, timestamp in cars %}
    <tr>
        <td>{{ url_for('view_car', id=id) | linkify }}</td>
        <td>{{ name }}</td>
        <td>{{ timestamp | render_timestamp }}</td>
    </tr>
{% endfor %}
</table>
{% endif %}

{% if fuels %}
<h4>Fuels</h4>
<table>
    <tr>
        <th></th>
        <th></th>
        <th>score</th>
    </tr>
{% for fuel_id, car_id, score, timestamp in fuels %}
    <tr>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{{ url_for('view_car', id=car_id) | linkify }}</td>
        <td>{{ score }}</td>
        <td>{{ timestamp | render_timestamp }}</td>
    </tr>
{% endfor %}
{% endif %}
</table>

{% if fuel_submissions %}
<h4>Fuel submissions</h4>
<table>
{% for id, fuel_id, successful, t in fuel_submissions %}
    <tr>
        <td>{{ url_for('view_fuel_submission', id=id) | linkify }}</td>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{% if successful %}ok{% else %}failed{% endif %}</td>
        <td>{{ t | render_timestamp }}</td>
    </tr>
{% endfor %}
</table>
{% endif %}
{% endblock %}
'''
