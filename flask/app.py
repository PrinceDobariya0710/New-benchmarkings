import os
from collections import namedtuple
from operator import attrgetter
import random
from email.utils import formatdate

import flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session

# Database configuration
DBDRV  = "postgresql"
DBNAME = os.getenv('PGDB', 'benchmark_db')
DBHOST = os.getenv('PGHOST', 'localhost')
DBUSER = os.getenv('PGUSER', 'postgres')
DBPSWD = os.getenv('PGPASS', 'root')

# Setup Flask and SQLAlchemy
app = flask.Flask(__name__)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = f"{DBDRV}://{DBUSER}:{DBPSWD}@{DBHOST}:5432/{DBNAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
with app.app_context():
    # Perform any database operations or session initialization here
    Session = scoped_session(sessionmaker(bind=db.engine))

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
    return flask.json.dumps(jdict), { "Content-Type": "application/json" }

# Models using SQLAlchemy
class World(db.Model):
    __tablename__ = 'world'
    id = Column(Integer, primary_key=True)
    randomnumber = Column(Integer, nullable=False)

    def to_dict(self):
        return {"id": self.id, "randomNumber": self.randomnumber}

class Fortune(db.Model):
    __tablename__ = 'fortune'
    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String, nullable=False)

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

@app.route("/json")
def json_data():
    return flask.jsonify(message="Hello, World!")

@app.route("/json-raw")
def json_data_raw():
    return jsonify({"message": "Hello, World!"})

@app.route("/db")
def get_random_world_single():
    wid = random.randint(1, 10000)
    session = Session()
    try:
        world = session.query(World).get(wid)
        return jsonify(world.to_dict())
    finally:
        session.close()

@app.route("/dbs")
def get_random_world():
    session = Session()
    try:
        worlds = [session.query(World).get(ident).to_dict() for ident in generate_ids(get_num_queries())]
        return jsonify(worlds)
    finally:
        session.close()

@app.route("/fortunes")
def get_fortunes():
    session = Session()
    try:
        fortunes = session.query(Fortune).all()
        tmp_fortune = namedtuple("Fortune", ["id", "message"])
        fortunes.append(tmp_fortune(id=0, message="Additional fortune added at request time."))
        fortunes.sort(key=attrgetter("message"))
        return flask.render_template("fortunes.html", fortunes=fortunes)
    finally:
        session.close()

@app.route("/updates")
def updates():
    num_queries = get_num_queries()
    ids = generate_ids(num_queries)
    ids.sort()
    session = Session()
    try:
        worlds = []
        for ident in ids:
            world = session.query(World).get(ident)
            world.randomnumber = random.randint(1, 10000)
            worlds.append({"id": world.id, "randomNumber": world.randomnumber})
        session.commit()
        return jsonify(worlds)
    finally:
        session.close()

@app.route("/plaintext")
def plaintext():
    response = flask.make_response(b"Hello, World!")
    response.content_type = "text/plain"
    return response

