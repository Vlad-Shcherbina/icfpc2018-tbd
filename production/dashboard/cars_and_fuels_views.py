import json

import flask

from production.dashboard import app, get_conn

@app.route('/cars')
def list_cars():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT cars.id, cars.name, cars.data, invocations.id, invocations.data
        FROM cars
        JOIN invocations ON cars.invocation_id = invocations.id
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
    <th>invocation</th>
</tr>
{% for id, name, data, inv_id, inv_data in cur %}
    <tr>
        <td>{{ url_for('view_car', id=id) | linkify }}</td>
        <td>{{ name }}</tb>
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
        'SELECT id, name, data, invocation_id FROM cars WHERE id = %s',
        [id])
    [car_id, car_name, car_data, inv_id] = cur.fetchone()
    cur.execute(
        'SELECT data FROM invocations WHERE id = %s',
        [inv_id])
    [inv_data] = cur.fetchone()

    return flask.render_template_string(VIEW_CAR_TEMPLATE, **locals())

VIEW_CAR_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Car info</h3>
Produced by {{ inv_data | render_invocation(inv_id) }} <br><br>
Name: {{ car_name }} <br>
Data:
<pre>{{ car_data | json_dump }}</pre>

</table>
{% endblock %}
'''
