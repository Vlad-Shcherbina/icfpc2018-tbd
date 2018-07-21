import json
import zlib
from collections import defaultdict

import flask

from production.dashboard import app, get_conn


@app.route('/problems')
def list_problems():
    prefix = flask.request.args.get('prefix', '')

    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            problems.id, problems.name,
            problems.src_data IS NOT NULL, problems.tgt_data IS NOT NULL,
            problems.stats, problems.invocation_id,
            traces.id, traces.scent, traces.status, traces.energy, traces.invocation_id,
            traces.data IS NOT NULL
        FROM problems
        LEFT OUTER JOIN traces ON traces.problem_id = problems.id
        WHERE problems.name LIKE %s
        ORDER BY problems.id DESC, traces.id DESC
    ''', [prefix + '%'])
    rows = cur.fetchall()
    best_by_problem = defaultdict(lambda: float('+inf'))
    for [problem_id, _, _, _, _, _, _, _, _,  energy, _, _] in rows:
        if energy is not None:
            best_by_problem[problem_id] = min(best_by_problem[problem_id], energy)

    return flask.render_template_string(LIST_PROBLEMS_TEMPLATE, **locals())

LIST_PROBLEMS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All problems</h3>
<table id='t'>
{% for problem_id, problem_name, has_src, has_tgt, problem_stats, problem_inv_id,
       trace_id, trace_scent, trace_status, trace_energy, trace_inv_id,
       trace_has_data in rows %}
    <tr>
        <td>{{ url_for('view_invocation', id=problem_inv_id) | linkify }}</td>
        <td>
            {{ url_for('view_problem', id=problem_id) | linkify }}
            {% if has_src %}
                (<a href="{{ url_for('visualize_model', id=problem_id, which='src')}}"
                 >vis src</a>)
            {% endif %}
            {% if has_tgt %}
                (<a href="{{ url_for('visualize_model', id=problem_id, which='tgt')}}"
                 >vis tgt</a>)
            {% endif %}
        </td>
        <td>{{ problem_name }}</td>
        <td>{{ problem_stats }}</td>
        {% if trace_id is not none %}
            <td>
                {{ url_for('view_trace', id=trace_id) | linkify }}
                {% if trace_has_data %}
                    (<a href="{{ url_for('visualize_trace', id=trace_id)}}">vis</a>)
                {% endif %}
            </td>
            <td>{{ trace_status }}</td>
            <td>
                {% if best_by_problem[problem_id] == trace_energy %}
                    <b>{{ trace_energy }}</b>
                {% else %}
                    {{ trace_energy }}
                {% endif %}
            </td>
            <td>
                {% if best_by_problem[problem_id] == trace_energy %}
                    <b>{{ trace_scent }}</b>
                {% else %}
                    {{ trace_scent }}
                {% endif %}
            </td>
            <td>{{ url_for('view_invocation', id=trace_inv_id) | linkify }}</td>
        {% endif %}
    </tr>
{% endfor %}
</table>

<script src='/static/merge_equal_td.js'></script>
<script>
    mergeEqualTd(document.getElementById('t'), [[0], [1, 2, 3], [4]]);
</script>
{% endblock %}
'''


@app.route('/problem/<int:id>')
def view_problem(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            name,
            src_data IS NOT NULL,
            tgt_data IS NOT NULL,
            stats, extra, invocation_id, timestamp
        FROM problems WHERE id = %s''',
        [id])
    [name, has_src, has_tgt, stats, extra, inv_id, timestamp] = cur.fetchone()

    cur.execute('''
        SELECT id, scent, status, energy, invocation_id, timestamp
        FROM traces
        WHERE problem_id = %s
        ORDER BY id DESC
        ''',
        [id])
    traces = cur.fetchall()
    return flask.render_template_string(VIEW_PROBLEM_TEMPLATE, **locals())

VIEW_PROBLEM_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Problem info</h3>
Name: {{ name }} <br>
Produced by {{ url_for('view_invocation', id=inv_id) | linkify }} <br><br>
Stats: {{ stats }} <br>
Time: {{ timestamp | render_timestamp }} <br>
Extra:
<pre>{{ extra | json_dump }}</pre>

{% if has_src %}
  (<a href="{{ url_for('visualize_model', id=id, which='src') }}">vis src</a>)
{% endif %}
{% if has_tgt %}
  (<a href="{{ url_for('visualize_model', id=id, which='tgt') }}">vis tgt</a>)
{% endif %}

{% if traces %}
<h4>Traces</h4>
<table>
{% for trace_id, trace_scent, trace_status, trace_energy, trace_inv_id, trace_t in traces %}
    <tr>
        <td>{{ url_for('view_trace', id=trace_id) | linkify}}</td>
        <td>{{ trace_status }}</td>
        <td>{{ trace_energy }}</td>
        <td>{{ trace_t | render_timestamp }}</td>
        <td>{{ trace_scent }}</td>
        <td>{{ url_for('view_invocation', id=trace_inv_id) | linkify }}</td>
    </tr>
{% endfor %}
</table>
{% endif %}
{% endblock %}
'''


@app.route('/trace/<int:id>')
def view_trace(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT problem_id, scent, status, energy, extra, invocation_id '
        'FROM traces WHERE id = %s',
        [id])
    [problem_id, scent, status, energy, extra, inv_id] = cur.fetchone()

    return flask.render_template_string(VIEW_TRACE_TEMPLATE, **locals())

VIEW_TRACE_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Trace info</h3>
Status: {{ status }} <br>
Scent: {{ scent }} <br>
Energy: {{ energy }} <br>
Problem: {{ url_for('view_problem', id=problem_id) | linkify }} <br>
Produced by {{ url_for('view_invocation', id=inv_id) | linkify }} <br><br>
Extra:
<pre>{{ extra | json_dump }}</pre>

{% if extra.get('solver', {}).get('tb') %}
<pre>{{ extra.get('solver', {}).get('tb') }}</pre>
{% endif %}

<a href="{{ url_for('visualize_trace', id=id) }}">visualize</a>
{% endblock %}
'''


@app.route('/vis_model/<int:id>')
def visualize_model(id):
    which = flask.request.args['which']
    conn = get_conn()
    cur = conn.cursor()

    if which == 'src':
        cur.execute(
            'SELECT src_data '
            'FROM problems WHERE id = %s',
            [id])
    elif which == 'tgt':
        cur.execute(
            'SELECT tgt_data '
            'FROM problems WHERE id = %s',
            [id])
    else:
        assert False, which

    [data] = cur.fetchone()
    data = zlib.decompress(data)

    return flask.render_template('visualize_model.html', data=list(map(int, data)))


@app.route('/vis_trace/<int:id>')
def visualize_trace(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT model_id, data '
        'FROM traces WHERE id = %s',
        [id])
    [model_id, trace_data] = cur.fetchone()
    trace_data = zlib.decompress(trace_data)

    cur.execute(
        'SELECT data '
        'FROM models WHERE id = %s',
        [model_id])
    [model_data] = cur.fetchone()
    model_data = zlib.decompress(model_data)

    return flask.render_template(
        'visualize_trace.html',
        model_data=list(map(int, model_data)),
        trace_data=list(map(int, trace_data)))

