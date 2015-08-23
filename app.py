from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
import os
import requests
from nltk.corpus import stopwords
from collections import Counter
from bs4 import BeautifulSoup
import operator
import re
import nltk
from rq import Queue
from rq.job import Job
from worker import conn
from flask import jsonify

##################
# initialization #
##################
nltk.data.path.append('./nltk_data')
stops = stopwords.words('english')

#################
# configuration #
#################
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)
q = Queue(connection=conn)

##########
# helper #
##########
def count_and_save_words(url):
    errors = []
    try:
        r = requests.get(url)
    except:
        errors.append("Unable to get URL. Please make sure it's valid and try again.")
        return {"error": errors}

    # text processing
    raw = BeautifulSoup(r.text, 'html.parser').get_text()
    nltk.data.path.append('./nltk_data/')
    tokens = nltk.word_tokenize(raw)
    text = nltk.Text(tokens)

    # remove punctuation, count raw words
    nonPunct = re.compile('.*[A-Za-z].*')
    raw_words = [w for w in text if nonPunct.match(w)]
    raw_words_count = Counter(raw_words)

    # stop words
    no_stop_words = [w for w in raw_words if w.lower() not in stops]
    no_stop_words_count = Counter(no_stop_words)

    # save the results
    from models import Result
    try:
        result = Result(
                url=url,
                result_all=raw_words_count,
                result_no_stop_words=no_stop_words_count)
        db.session.add(result)
        db.session.commit()
        return result.id
    except Exception as e:
        errors.append("Unable to add item to database: {}".format(e))
        return {"error": errors}
    print("Done!!")

##########
# routes #
##########
@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}
    if request.method == "POST":
        url = request.form['url']
        if 'http://' not in url[:7].lower():
            url = 'http://' + url
        job = q.enqueue_call(
                func='app.count_and_save_words', args=(url,), result_ttl=5000)
        print("JOB ID: {}".format(job.get_id()))
    return render_template('index.html', results=results)

@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):
    from models import Result
    job = Job.fetch(job_key, connection=conn)
    if job.is_finished:
        result = Result.query.filter_by(id=job.result)[0]
        results = sorted(
                result.result_no_stop_words.items(),
                key=operator.itemgetter(1),
                reverse=True
                )[:10]
        return jsonify(results)
    else:
        return "Nay!", 202

if __name__ == "__main__":
    app.run(host="0.0.0.0")
