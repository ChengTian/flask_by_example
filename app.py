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

##########
# routes #
##########
@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = {}
    if request.method == "POST":
        try:
            url = request.form['url']
            r = requests.get(url)
        except Exception as e:
            print(e)
            errors.append("Unable to get URL. Please make sure it's valid and try again.")
            return render_template('index.html', errors=errors)
        if r:
            # text processing
            raw = BeautifulSoup(r.text, 'html.parser').get_text()
            tokens = nltk.word_tokenize(raw)
            text = nltk.Text(tokens)

            # remove punctuation and count raw words
            nonPunct = re.compile('.*[A-Za-z].*')
            raw_words = [w for w in text if nonPunct.match(w)]
            raw_words_count = Counter(raw_words)

            # stop words
            no_stop_words = [w for w in raw_words if w.lower() not in stops]
            no_stop_words_count = Counter(no_stop_words)

            # save the results
            results = sorted(
                    no_stop_words_count.items(),
                    key=lambda pair: pair[1],
                    reverse=True)[:10]
            try:
                from models import Result
                result = Result(
                        url=url,
                        result_all=raw_words_count,
                        result_no_stop_words=no_stop_words_count)
                db.session.add(result)
                db.session.commit()
            except Exception as e:
                print(e)
                errors.append("Unable to add item to database.")
    return render_template('index.html', errors=errors, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
