import json
import zlib
from collections import defaultdict

import flask

from production.dashboard import app, get_conn
from production.dashboard.flask_utils import memoized_render_template_string

@app.route('/problems.json')
def list_problems_json():
    prefix = flask.request.args.get('prefix', '')

    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            problems.id, problems.name,
            problems.src_data IS NOT NULL as has_src, problems.tgt_data IS NOT NULL as has_tgt,
            problems.stats, problems.invocation_id as prob_inv_id,
            traces.id as trace_id, traces.scent, traces.status, traces.energy, traces.invocation_id as trace_inv_id,
            traces.data IS NOT NULL as has_data, traces.extra
        FROM problems
        LEFT OUTER JOIN traces ON traces.problem_id = problems.id
        WHERE problems.name LIKE %s
        ORDER BY problems.id DESC, traces.id DESC
    ''', [prefix + '%'])
    return json.dumps({
        "columns": [column[0] for column in cur.description],
        "data": list(cur)
    })

    return flask.render_template_string(LIST_PROBLEMS_TEMPLATE, **locals())

@app.route('/problems')
def list_problems():
    prefix = flask.request.args.get('prefix', '')

    return memoized_render_template_string(LIST_PROBLEMS_TEMPLATE, **locals())

LIST_PROBLEMS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<script
  src="https://code.jquery.com/jquery-3.3.1.min.js"
  integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8="
  crossorigin="anonymous"></script>
<script src='/static/merge_equal_td.js'></script>
<script src="/static/fetch_db.js"></script>
<h3>All problems</h3>
<div id='desc'></div>
<table id='t'>
</table>
<script>fetch_db('/problems.json?prefix={{ prefix }}', '#t', '#desc')</script>

<script>
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
    best_energy = min(
        (energy for _, _, _, energy, _, _ in traces if energy is not None),
        default=-1)
    return memoized_render_template_string(VIEW_PROBLEM_TEMPLATE, **locals())

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
        <td>
            {% if best_energy == trace_energy %}
                <b>{{ trace_energy }}</b>
            {% else %}
                {{ trace_energy }}
            {% endif %}
        </td>
        <td>{{ trace_t | render_timestamp }}</td>
        <td>
            {% if best_energy == trace_energy %}
                <b>{{ trace_scent }}</b>
            {% else %}
                {{ trace_scent }}
            {% endif %}
        </td>
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

    return memoized_render_template_string(VIEW_TRACE_TEMPLATE, **locals())

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
        'SELECT problem_id, data '
        'FROM traces WHERE id = %s',
        [id])
    [problem_id, trace_data] = cur.fetchone()
    trace_data = zlib.decompress(trace_data)
    trace_data = list(map(int, trace_data))

    cur.execute(
        'SELECT src_data, tgt_data '
        'FROM problems WHERE id = %s',
        [problem_id])
    [src_data, tgt_data] = cur.fetchone()
    if src_data is not None:
        src_data = zlib.decompress(src_data)
        src_data = list(map(int, src_data))
    if tgt_data is not None:
        tgt_data = zlib.decompress(tgt_data)
        tgt_data = list(map(int, tgt_data))

    return flask.render_template(
        'visualize_trace.html',
        src_data=src_data,
        tgt_data=tgt_data,
        trace_data=trace_data)
