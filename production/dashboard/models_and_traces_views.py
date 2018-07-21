import json
import zlib
from collections import defaultdict

import flask

from production.dashboard import app, get_conn


@app.route('/models')
def list_models():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            models.id, models.name, models.stats, models.invocation_id,
            traces.id, traces.scent, traces.status, traces.energy, traces.invocation_id,
            traces.data IS NOT NULL
        FROM models
        LEFT OUTER JOIN traces ON traces.model_id = models.id
        ORDER BY models.id DESC, traces.id DESC
    ''')
    rows = cur.fetchall()
    best_by_model = defaultdict(lambda: float('+inf'))
    for [model_id, _, _, _, _, _, _,  energy, _, _] in rows:
        if energy is not None:
            best_by_model[model_id] = min(best_by_model[model_id], energy)

    return flask.render_template_string(LIST_MODELS_TEMPLATE, **locals())

LIST_MODELS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All models</h3>
<table id='t'>
{% for model_id, model_name, model_stats, model_inv_id,
       trace_id, trace_scent, trace_status, trace_energy, trace_inv_id,
       trace_has_data in rows %}
    <tr>
        <td>{{ url_for('view_invocation', id=model_inv_id) | linkify }}</td>
        <td>
            {{ url_for('view_model', id=model_id) | linkify }}
            (<a href="{{ url_for('visualize_model', id=model_id)}}">vis</a>)
        </td>
        <td>{{ model_name }}</td>
        <td>{{ model_stats }}</td>
        {% if trace_id is not none %}
            <td>
                {{ url_for('view_trace', id=trace_id) | linkify }}
                {% if trace_has_data %}
                    (<a href="{{ url_for('visualize_trace', id=trace_id)}}">vis</a>)
                {% endif %}
            </td>
            <td>{{ trace_status }}</td>
            <td>
                {% if best_by_model[model_id] == trace_energy %}
                    <b>{{ trace_energy }}</b>
                {% else %}
                    {{ trace_energy }}
                {% endif %}
            </td>
            <td>
                {% if best_by_model[model_id] == trace_energy %}
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


@app.route('/model/<int:id>')
def view_model(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT stats, extra, invocation_id, timestamp '
        'FROM models WHERE id = %s',
        [id])
    [stats, extra, inv_id, timestamp] = cur.fetchone()

    cur.execute('''
        SELECT id, scent, status, energy, invocation_id, timestamp
        FROM traces
        WHERE model_id = %s
        ORDER BY id DESC
        ''',
        [id])
    traces = cur.fetchall()
    return flask.render_template_string(VIEW_MODEL_TEMPLATE, **locals())

VIEW_MODEL_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Model info</h3>
Produced by {{ url_for('view_invocation', id=inv_id) | linkify }} <br><br>
Stats: {{ stats }} <br>
Time: {{ timestamp | render_timestamp }} <br>
Extra:
<pre>{{ extra | json_dump }}</pre>

<a href="{{ url_for('visualize_model', id=id) }}">visualize</a>

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
        'SELECT model_id, scent, status, energy, extra, invocation_id '
        'FROM traces WHERE id = %s',
        [id])
    [model_id, scent, status, energy, extra, inv_id] = cur.fetchone()

    return flask.render_template_string(VIEW_TRACE_TEMPLATE, **locals())

VIEW_TRACE_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Trace info</h3>
Status: {{ status }} <br>
Scent: {{ scent }} <br>
Energy: {{ energy }} <br>
Model: {{ url_for('view_model', id=model_id) | linkify }} <br>
Produced by {{ url_for('view_invocation', id=inv_id) | linkify }} <br><br>
Extra:
<pre>{{ extra | json_dump }}</pre>

<a href="{{ url_for('visualize_trace', id=id) }}">visualize</a>
{% endblock %}
'''


@app.route('/vis_model/<int:id>')
def visualize_model(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT data '
        'FROM models WHERE id = %s',
        [id])
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

