#!/usr/bin/env python
import os
import sys
import multiprocessing
import itertools
from collections import namedtuple
from operator import attrgetter, itemgetter
import random
from email.utils import formatdate

import flask
from pony import orm


if sys.version_info[0] == 3:
    xrange = range
    
_is_travis = os.environ.get('TRAVIS') == 'true'

_is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")

_cpu_count = multiprocessing.cpu_count()
if _is_travis:
    _cpu_count = 2

_raw = os.getenv('USE_RAW', "0") == "1"


import orjson as json


DBDRV  = "postgres"
DBNAME = os.getenv('PGDB', 'benchmark_db')
DBHOST = os.getenv('PGHOST', 'localhost')
DBUSER = os.getenv('PGUSER', 'postgres')
DBPSWD = os.getenv('PGPASS', 'root')

# setup

app = flask.Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

# -----------------------------------------------------------------------------
response_server = None
response_add_date = False

@app.after_request
def after_request(response):
    if response_server:
        response.headers['Server'] = response_server
    if response_add_date:
        response.headers['Date'] = formatdate(timeval=None, localtime=False, usegmt=True)
    return response

def jsonify(jdict):
    return json.dumps(jdict), { "Content-Type": "application/json" }

# -----------------------------------------------------------------------------

def get_num_queries():
    try:
        num_queries = flask.request.args.get("queries", 1, type=int)
    except ValueError:
        num_queries = 1
    if num_queries < 1:
        return 1
    if num_queries > 500:
        return 500
    return num_queries

def generate_ids(num_queries):
    return random.sample(range(1, 10001), num_queries)


if _raw:
    import jinja2
    from psycopg2.pool import ThreadedConnectionPool
    from psycopg2.extras import execute_batch

    pool_size = int(_cpu_count * 2.5 / 4)
    if _is_travis:
        pool_size = 5
    
    POOL = ThreadedConnectionPool(
        minconn=pool_size,
        maxconn=pool_size,
        database=DBNAME,
        user=DBUSER,
        password=DBPSWD,
        host=DBHOST,
        port=5432,
    )
    read_row_sql = (
        'SELECT world."randomnumber", world."id" FROM "world" WHERE id = %(id)s'
    )
    prepared_read_row_sql = (
        'SELECT world."randomnumber", world."id" FROM "world" WHERE id = $1'
    )
    write_row_sql = 'UPDATE "world" SET "randomnumber"=$1 WHERE id=$2'
    ADDITIONAL_ROW = (0, "Additional fortune added at request time.")
    db = POOL.getconn()
    cursor = db.cursor()
    cursor.execute("PREPARE read_stmt (int) AS " + prepared_read_row_sql)
    cursor.execute("PREPARE write_stmt (int, int) AS " + write_row_sql)
    cursor.execute('PREPARE fortune AS SELECT * FROM "Fortune"')
    del cursor
    POOL.putconn(db)
    del db

    def db_query(arg):
        (cursor, ident) = arg
        cursor.execute("EXECUTE read_stmt(%s)", [ident])
        result = cursor.fetchone()
        return result
        
    fn = os.path.join("templates", "fortune_raw.html")
    with open(fn, "r") as template_file:
        template_text = template_file.read()
    FORTUNE_TEMPLATE = jinja2.Template(template_text)
    #Fortune = namedtuple("Fortune", ["id", "message"])

else: # --------- PonyORM ------------------------------------------------
    app.config["STORM_DATABASE_URI"] = f"{DBDRV}://{DBUSER}:{DBPSWD}@{DBHOST}:5432/{DBNAME}"
    db = orm.Database()
    db.bind(DBDRV, host=DBHOST, port=5432, user=DBUSER, password=DBPSWD, database=DBNAME)

    class World(db.Entity):
        _table_ = "world"
        id = orm.PrimaryKey(int)
        randomNumber = orm.Required(int, column="randomnumber")

        def to_dict(self):
            """Return object data in easily serializeable format"""
            return {"id": self.id, "randomNumber": self.randomNumber}

    class Fortune(db.Entity):
        _table_ = "fortune"
        id = orm.PrimaryKey(int, auto=True)
        message = orm.Required(str)

    db.generate_mapping(create_tables=False)
    
# ----------------------------------------------------------------------------------------

@app.route("/json")
def json_data():
    return flask.jsonify(message="Hello, World!")


@app.route("/json-raw")
def json_data_raw():
    return jsonify( {"message": "Hello, World!"} )


@app.route("/db")
def get_random_world_single():
    wid = random.randint(1, 10000)
    with orm.db_session(serializable=False):
        world = World[wid]
    return jsonify(world.to_dict())


@app.route("/db-raw")
def get_random_world_single_raw():
    db = POOL.getconn()
    cursor = db.cursor()
    cursor.execute("EXECUTE read_stmt(%s)", generate_ids(1))
    result = cursor.fetchone()
    world = {"id": result[0], "randomNumber": result[1]}
    POOL.putconn(db)
    return jsonify(world)


@app.route("/dbs")
def get_random_world():
    with orm.db_session(serializable=False):
        worlds = [World[ident].to_dict() for ident in generate_ids(get_num_queries())]
    return jsonify(worlds)


@app.route("/query-raw")
def get_random_world_raw():
    db = POOL.getconn()
    cursor = db.cursor()
    num_queries = get_num_queries()
    results = map(db_query, zip(itertools.repeat(cursor, num_queries), generate_ids(num_queries)))
    worlds = [ {"id": result[0], "randomNumber": result[1]} for result in results ]
    POOL.putconn(db)
    return jsonify(worlds)


@app.route("/fortunes")
def get_fortunes():
    with orm.db_session(serializable=False):
        fortunes = list(Fortune.select()[:])
        #fortunes = list(orm.select(fortune for fortune in Fortune))
    tmp_fortune = namedtuple("Fortune", ["id", "message"])
    fortunes.append(
        tmp_fortune(id=0, message="Additional fortune added at request time.")
    )
    fortunes.sort(key=attrgetter("message"))
    return flask.render_template("fortunes.html", fortunes=fortunes)


@app.route("/fortunes-raw")
def get_fortunes_raw():
    db = POOL.getconn()
    cursor = db.cursor()
    cursor.execute("EXECUTE fortune")
    fortunes = list(cursor.fetchall())
    fortunes.append(ADDITIONAL_ROW)
    fortunes.sort(key=itemgetter(1))
    POOL.putconn(db)
    return flask.Response(FORTUNE_TEMPLATE.render(fortunes=fortunes))


@app.route("/updates")
def updates():
    num_queries = get_num_queries()
    ids = generate_ids(num_queries)
    ids.sort()
    worlds = []
    with orm.db_session(serializable=False):
        for ident in ids:
            world = World[ident]
            world.randomNumber = random.randint(1, 10000)
            worlds.append({"id": world.id, "randomNumber": world.randomNumber})
    return jsonify(worlds)


@app.route("/updates-raw")
def updates_raw():
    db = POOL.getconn()
    cursor = db.cursor()
    num_queries = get_num_queries()
    ids = generate_ids(num_queries)
    update_values = generate_ids(num_queries)
    list(map(db_query, zip(itertools.repeat(cursor, num_queries), generate_ids(num_queries))))
    worlds = list(zip(ids, update_values))
    execute_batch(cursor, "EXECUTE write_stmt(%s, %s)", worlds)
    db.commit()
    POOL.putconn(db)
    data = [ {"id": ident, "randomNumber": update} for ident, update in worlds ]
    return jsonify(data)


@app.route("/plaintext")
def plaintext():
    response = flask.make_response(b"Hello, World!")
    response.content_type = "text/plain"
    return response

# -----------------------------------------------------------------------------------

if __name__ == "__main__":
    import optparse
    import logging
    import signal
    import re

    parser = optparse.OptionParser("usage: %prog [options]", add_help_option=False)
    parser.add_option("-h", "--host", dest="host", default='0.0.0.0', type="string")
    parser.add_option("-p", "--port", dest="port", default=8080, type="int")
    parser.add_option("-s", "--server", dest="server", default="gunicorn", type="string")
    parser.add_option("-w", "--workers", dest="workers", default=0, type="int")
    parser.add_option("-k", "--keepalive", dest="keepalive", default=60, type="int")
    parser.add_option("-v", "--verbose", dest="verbose", default=0, type="int")
    (opt, args) = parser.parse_args() 

    workers = opt.workers if opt.workers > 0 else _cpu_count

    if _is_travis:
        workers = 2

    worker_list = [ ]

    def run_app():
        global response_server
        global response_add_date
        app.run(debug=True)

    def create_fork():
        pid = os.fork()
        if pid > 0:            
            return pid
        try:
            run_app()
        except KeyboardInterrupt:
            pass
        sys.exit(0)

    for i in range(0, workers):
        pid = create_fork()
        print("Worker process added with PID:", pid)
        worker_list.append(pid)

    print("Running {} workers".format(len(worker_list)))
    try:
        for i in range(workers):
            os.wait()
    except KeyboardInterrupt:
        print("\n" + "Stopping all workers")
        for pid in worker_list:
            os.kill(pid, signal.SIGINT)

