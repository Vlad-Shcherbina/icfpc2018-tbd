import json

import flask

from production.dashboard import app, get_conn

@app.route('/cars')
def list_cars():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            cars.id, cars.name, cars.data,
            COUNT(fuels.id), COUNT(fuels.score),
            invocations.id, invocations.data,
            cars.timestamp
        FROM cars
        JOIN invocations ON cars.invocation_id = invocations.id
        LEFT OUTER JOIN fuels ON fuels.car_id = cars.id
        GROUP BY cars.id, invocations.id
        ORDER BY cars.id DESC
        ''')
    return flask.render_template_string(LIST_CARS_TEMPLATE, **locals())

LIST_CARS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All cars</h3>
<table>
<tr>
    <th>car</th>
    <th>name</th>
    <th>num. attempts</th>
    <th>num. fuels</th>
    <th>time</th>
    <th>invocation</th>
</tr>
{% for id, name, data, num_attempts, num_solutions, inv_id, inv_data, timestamp in cur %}
    <tr>
        <td>{{ url_for('view_car', id=id) | linkify }}</td>
        <td>{{ name }}</td>
        <td>{{ num_attempts }}</td>
        <td>{{ num_solutions }}</td>
        <td>{{ timestamp | render_timestamp }}</td>
        <td>{{ inv_data | render_invocation(inv_id) }}</td>
    </tr>
{% endfor %}
</table>
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
        SELECT fuels.id, fuels.score, fuels.timestamp, invocations.id, invocations.data
        FROM fuels
        JOIN invocations ON fuels.invocation_id = invocations.id
        WHERE fuels.car_id = %s
        ORDER BY fuels.id DESC
        ''',
        [id])
    fuels = cur.fetchall()

    return flask.render_template_string(VIEW_CAR_TEMPLATE, **locals())

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
<table>
<tr>
    <td></td>
    <td>score</td>
</tr>
{% for fuel_id, score, t, inv_id, inv_data in fuels %}
    <tr>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{{ score }}</td>
        <td>{{ t | render_timestamp }}</td>
        <td>{{ inv_data | render_invocation(inv_id) }}</td>
    </tr>
{% endfor %}
</table>
{% endif %}

</table>
{% endblock %}
'''


@app.route('/fuels')
def list_fuels():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            fuels.id, fuels.score,
            cars.id,
            invocations.id, invocations.data,
            fuels.timestamp
        FROM fuels
        JOIN cars ON fuels.car_id = cars.id
        JOIN invocations ON fuels.invocation_id = invocations.id
        ORDER BY fuels.id DESC
        ''')
    return flask.render_template_string(LIST_FUELS_TEMPLATE, **locals())

LIST_FUELS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All fuels</h3>
<table>
<tr>
    <th>fuel</th>
    <th>score</th>
    <th>car</th>
    <th>time</th>
    <th>invocation</th>
</tr>
{% for fuel_id, score, car_id, inv_id, inv_data, timestamp in cur %}
    <tr>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{{ score }}</td>
        <td>{{ url_for('view_car', id=car_id) | linkify }}</td>
        <td>{{ timestamp | render_timestamp }}</td>
        <td>{{ inv_data | render_invocation(inv_id) }}</td>
    </tr>
{% endfor %}
</table>
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
        ''',
        [id])
    submissions = cur.fetchall()

    return flask.render_template_string(VIEW_FUEL_TEMPLATE, **locals())

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
            fuel_submissions.data IS NOT NULL,
            invocations.id,
            invocations.data,
            fuel_submissions.timestamp
        FROM fuel_submissions
        JOIN fuels ON fuel_submissions.fuel_id = fuels.id
        JOIN invocations ON fuel_submissions.invocation_id = invocations.id
        ORDER BY fuel_submissions.id DESC
        ''')
    return flask.render_template_string(LIST_FUEL_SUBMISSIONS_TEMPLATE, **locals())

LIST_FUEL_SUBMISSIONS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All fuel submissions</h3>
<table>
{% for id, fuel_id, car_id, successful, inv_id, inv_data, timestamp in cur %}
    <tr>
        <td>{{ url_for('view_fuel_submission', id=id) | linkify }}</td>
        <td>{{ url_for('view_fuel', id=fuel_id) | linkify }}</td>
        <td>{{ url_for('view_car', id=car_id) | linkify }}</td>
        <td>{% if successful %}failed{% else %}ok{% endif %}</td>
        <td>{{ timestamp | render_timestamp }}</td>
        <td>{{ inv_data | render_invocation(inv_id) }}</td>
    </tr>
{% endfor %}
</table>
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
    print(data, type(data))
    print(extra, type(extra))

    return flask.render_template_string(VIEW_FUEL_SUBMISSION_TEMPLATE, **locals())

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
