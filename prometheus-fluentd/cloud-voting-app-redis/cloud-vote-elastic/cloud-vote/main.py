from flask import Flask, request, render_template
from elasticapm.contrib.flask import ElasticAPM
from elasticapm.handlers.logging import Formatter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app, Counter
import os
import redis
import socket
import sys
import logging

app = Flask(__name__)

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("VOTE3VALUE" in os.environ and os.environ['VOTE3VALUE']):
    button3 = os.environ['VOTE3VALUE']
else:
    button3 = app.config['VOTE3VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis configurations
redis_server = os.environ['REDIS']

# Elastic APM Configurations
app.config['ELASTIC_APM'] = {
# Set required service name. Allowed characters:
# a-z, A-Z, 0-9, -, _, and space
'SERVICE_NAME': os.environ['SERVICE_NAME'],
#
# Use if APM Server requires a token
'SECRET_TOKEN': os.environ['SECRET_TOKEN'],
#
# Set custom APM Server URL (default: http://localhost:8200)
'SERVER_URL': os.environ['SERVER_URL'],
#
# Set environment
'ENVIRONMENT': os.environ['ENVIRONMENT'],
#
# Set prometheus_metrics
'PROMETHEUS_METRICS': os.environ['PROMETHEUS_METRICS'],
}
apm = ElasticAPM(app)

# Redis Connection
try:
    if "REDIS_PWD" in os.environ:
        r = redis.StrictRedis(host=redis_server,
                        port=6379,
                        password=os.environ['REDIS_PWD'])
    else:
        r = redis.Redis(redis_server)
    r.ping()
except redis.ConnectionError:
    exit('Failed to connect to Redis, terminating.')

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1): r.set(button1, 0)
if not r.get(button2): r.set(button2, 0)
if not r.get(button3): r.set(button3, 0)

# Elastic APM Log correlation settings
ch = logging.StreamHandler(sys.stdout)
logger = logging.getLogger('cloud-voting')
logger.setLevel(logging.INFO)
# We imported a custom Formatter from the Python Agent earlier
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# Define prometheus counter
VOTES = Counter('cloud_votes_total', 'Cloud Votes Requested.', labelnames=['vote'])

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':

        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        vote2 = r.get(button2).decode('utf-8')
        vote3 = r.get(button3).decode('utf-8')

        # Set logger
        logger.info('Page loading')

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), value3=int(vote3),
                               button1=button1, button2=button2, button3=button3, title=title)

    elif request.method == 'POST':

        # Increment Counter
        VOTES.labels(request.form['vote']).inc()

        if request.form['vote'] == 'reset':
            
            # Empty table and return results
            r.set(button1, 0)
            r.set(button2, 0)
            r.set(button3, 0)
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')
            vote3 = r.get(button3).decode('utf-8')

            # Set logger
            logger.info('Reset pushed')

            return render_template("index.html", value1=int(vote1), value2=int(vote2), value3=int(vote3),
                                   button1=button1, button2=button2, button3=button3, title=title)
        
        else:

            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote, 1)
            
            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')
            vote3 = r.get(button3).decode('utf-8')

            # Set logger
            logger.info('Voted {}'.format(vote))

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), value3=int(vote3),
                                   button1=button1, button2=button2, button3=button3, title=title)


if __name__ == "__main__":
    app.run()