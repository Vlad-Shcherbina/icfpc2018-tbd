import json

import flask

from production.dashboard import app, get_conn
from production.dashboard.flask_utils import memoized_render_template_string


@app.route('/cars')
def list_cars():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            cars.id, cars.name, cars.invocation_id, cars.timestamp,
            fuels.id, fuels.score,
            fuel_submissions.id, fuel_submissions.data IS NOT NULL
        FROM cars
        LEFT OUTER JOIN fuels ON fuels.car_id = cars.id
        LEFT OUTER JOIN fuel_submissions ON fuel_submissions.fuel_id = fuels.id
        ORDER BY cars.id DESC, fuels.id DESC, fuel_submissions.id DESC
    ''')
    return memoized_render_template_string(LIST_CARS_TEMPLATE, **locals())

LIST_CARS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All cars</h3>
<table id='t'>
{% for car_id, car_name, car_inv_id, car_t,
       fuel_id, fuel_score,
       sub_id, sub_ok in cur %}
    <tr>
        <td>{{ url_for('view_invocation', id=car_inv_id) | linkify }}</td>
        <td>{{ url_for('view_car', id=car_id) | linkify }}</td>
        <td>{{ car_name }}</td>
        <td>{{ car_t | render_timestamp }}</td>
        {% if fuel_id is not none %}
            <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
            <td>{% if fuel_score is not none %}{{ fuel_score }}
                {% else %}fail{% endif %}</td>
            {% if sub_id is not none %}
                <td>{{ url_for('view_fuel_submission', id=sub_id) | linkify}}</td>
                <td>{% if sub_ok %}ok{% else %}fail{% endif %}</td>
            {% endif %}
        {% endif %}
    </tr>
{% endfor %}
</table>

<script src='/static/merge_equal_td.js'></script>
<script>
    mergeEqualTd(document.getElementById('t'), [[0], [1, 2, 3], [4, 5]]);
</script>
{% endblock %}
'''


@app.route('/car/<int:id>')
def view_car(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT name, data, invocation_id, timestamp FROM cars WHERE id = %s',
        [id])
    [car_name, car_data, inv_id, timestamp] = cur.fetchone()
    cur.execute(
        'SELECT data FROM invocations WHERE id = %s',
        [inv_id])
    [inv_data] = cur.fetchone()

    cur.execute('''
        SELECT
            fuels.id, fuels.score, fuels.timestamp, fuels.invocation_id,
            fuel_submissions.id, fuel_submissions.data IS NOT NULL
        FROM fuels
        LEFT OUTER JOIN fuel_submissions
        ON fuels.id = fuel_submissions.fuel_id
        WHERE fuels.car_id = %s
        ORDER BY fuels.id DESC, fuel_submissions.id DESC
        ''',
        [id])
    fuels = cur.fetchall()

    return memoized_render_template_string(VIEW_CAR_TEMPLATE, **locals())

VIEW_CAR_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Car info</h3>
Produced by {{ inv_data | render_invocation(inv_id) }} <br><br>
Name: {{ car_name }} <br>
Time: {{ timestamp | render_timestamp }} <br>
Data:
<pre>{{ car_data | json_dump }}</pre>

{% if fuels %}
<h4>Fuels</h4>
<table id='t'>
{% for fuel_id, score, t, inv_id,
       sub_id, sub_ok in fuels %}
    <tr>
        <td>{{ url_for('view_invocation', id=inv_id) | linkify }}</td>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{% if score is not none %}{{ score }}{% else %}fail{% endif %}</td>
        <td>{{ t | render_timestamp }}</td>
        {% if sub_id is not none %}
            <td>{{ url_for('view_fuel_submission', id=sub_id) | linkify }}</td>
            <td>{% if sub_ok %}ok{% else %}fail{% endif %}</td>
        {% endif %}
    </tr>
{% endfor %}
</table>
{% endif %}

<script src='/static/merge_equal_td.js'></script>
<script>
    mergeEqualTd(document.getElementById('t'), [[0, 1, 2, 3]]);
</script>
{% endblock %}
'''


@app.route('/fuels')
def list_fuels():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            fuels.id,
            fuels.score,
            fuels.car_id,
            fuels.invocation_id,
            fuels.timestamp,
            fuel_submissions.id,
            fuel_submissions.data IS NOT NULL
        FROM fuels
        LEFT OUTER JOIN fuel_submissions ON fuels.id = fuel_submissions.fuel_id
        ORDER BY fuels.id DESC, fuel_submissions.id DESC
        ''')
    return memoized_render_template_string(LIST_FUELS_TEMPLATE, **locals())

LIST_FUELS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All fuels</h3>
<table id='t'>
{% for fuel_id, score, car_id, fuel_inv_id, fuel_t,
       sub_id, sub_ok in cur %}
    <tr>
        <td>{{ url_for('view_invocation', id=fuel_inv_id) | linkify }}</td>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{% if score is not none %}{{ score }}{% else %}fail{% endif %}</td>
        <td>{{ url_for('view_car', id=car_id) | linkify }}</td>
        <td>{{ fuel_t | render_timestamp }}</td>
        {% if sub_id is not none %}
            <td>{{ url_for('view_fuel_submission', id=sub_id) | linkify }}</td>
            <td>{% if sub_ok %}ok{% else %}fail{% endif %}</td>
        {% endif %}
    </tr>
{% endfor %}
</table>

<script src='/static/merge_equal_td.js'></script>
<script>
    mergeEqualTd(document.getElementById('t'), [[0], [1, 2, 3, 4]]);
</script>
{% endblock %}
'''


@app.route('/fuel/<int:id>')
def view_fuel(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT data, score, extra, car_id, invocation_id, timestamp '
        'FROM fuels WHERE id = %s',
        [id])
    [fuel_data, fuel_score, extra, car_id, inv_id, timestamp] = cur.fetchone()
    cur.execute(
        'SELECT data FROM invocations WHERE id = %s',
        [inv_id])
    [inv_data] = cur.fetchone()

    cur.execute('''
        SELECT id, data IS NOT NULL, timestamp
        FROM fuel_submissions
        WHERE fuel_id = %s
        ORDER BY id DESC
        ''',
        [id])
    submissions = cur.fetchall()

    return memoized_render_template_string(VIEW_FUEL_TEMPLATE, **locals())

VIEW_FUEL_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Fuel info</h3>
Produced by {{ inv_data | render_invocation(inv_id) }} <br><br>
Car: {{ url_for('view_car', id=car_id) | linkify }} <br>
Score: {{ fuel_score }} <br>
Time: {{ timestamp | render_timestamp }} <br>
Data:
<pre>{{ fuel_data | json_dump }}</pre>
Extra:
<pre>{{ extra | json_dump }}</pre>

{% if submissions %}
<h4>Submissions</h4>
<table>
{% for id, successful, t in submissions %}
    <tr>
        <td>{{ url_for('view_fuel_submission', id=id) | linkify}}</td>
        <td>{% if successful %}ok{% else %}failed{% endif %}</td>
        <td>{{ t | render_timestamp }}</td>
    </tr>
{% endfor %}
</table>
{% endif %}
{% endblock %}
'''


@app.route('/fuel_subs')
def list_fuel_submissions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            fuel_submissions.id,
            fuel_submissions.fuel_id,
            fuels.car_id,
            fuels.score,
            fuel_submissions.data IS NOT NULL,
            fuel_submissions.invocation_id,
            fuel_submissions.timestamp
        FROM fuel_submissions
        JOIN fuels ON fuel_submissions.fuel_id = fuels.id
        ORDER BY fuel_submissions.id DESC
        ''')
    return memoized_render_template_string(LIST_FUEL_SUBMISSIONS_TEMPLATE, **locals())

LIST_FUEL_SUBMISSIONS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All fuel submissions</h3>
<table id='t'>
{% for id, fuel_id, car_id, score, is_ok, sub_inv_id, sub_t in cur %}
    <tr>
        <td>{{ url_for('view_invocation', id=sub_inv_id) | linkify }}</td>
        <td>{{ url_for('view_car', id=car_id) | linkify }}</td>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{{ score }}</td>
        <td>{{ url_for('view_fuel_submission', id=id) | linkify }}</td>
        <td>{% if is_ok %}ok{% else %}failed{% endif %}</td>
        <td>{{ sub_t | render_timestamp }}</td>
    </tr>
{% endfor %}
</table>

<script src='/static/merge_equal_td.js'></script>
<script>
    mergeEqualTd(document.getElementById('t'), [[0]]);
</script>
{% endblock %}
'''


@app.route('/fuel_sub/<int:id>')
def view_fuel_submission(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT data, extra, fuel_id, invocation_id, timestamp '
        'FROM fuel_submissions WHERE id = %s',
        [id])
    [data, extra, fuel_id, inv_id, timestamp] = cur.fetchone()
    cur.execute(
        'SELECT data FROM invocations WHERE id = %s',
        [inv_id])
    [inv_data] = cur.fetchone()
    cur.execute(
        'SELECT car_id FROM fuels WHERE id = %s',
        [fuel_id])
    [car_id] = cur.fetchone()

    return memoized_render_template_string(VIEW_FUEL_SUBMISSION_TEMPLATE, **locals())

VIEW_FUEL_SUBMISSION_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Fuel submission info</h3>
Produced by {{ inv_data | render_invocation(inv_id) }} <br><br>
Fuel: {{ url_for('view_fuel', id=fuel_id) | linkify }} <br>
Car: {{ url_for('view_car', id=car_id) | linkify }} <br>
Time: {{ timestamp | render_timestamp }} <br>
Data:
<pre>{{ data | json_dump }}</pre>
Extra:
<pre>{{ extra | json_dump }}</pre>

</table>
{% endblock %}
'''
