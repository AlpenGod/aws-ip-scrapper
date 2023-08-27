from flask import Flask, request, url_for, render_template, redirect
import requests
from flask_table import Table, Col
from flask_wtf.csrf import CSRFProtect
import os

csrf = CSRFProtect()
app = Flask(__name__)
secret_key = os.environ.get('FLASK_SECRET_KEY')
app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE = "Strict"
)
csrf.init_app(app)
url = 'https://ip-ranges.amazonaws.com/ip-ranges.json'

r = requests.get(url)
ip_list = r.json()["prefixes"]
service_list = ["S3", "ROUTE53"]
res = [d for d in ip_list if d['service'] in service_list]


class SortableTable(Table):
    ip_prefix = Col('IP')
    service = Col('Service')
    allow_sort = True

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('index', sort=col_key, direction=direction)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        return redirect(f"/search?query_filter={request.form['search']}")
    sort = request.args.get('sort', 'service')
    reverse = (request.args.get('direction', 'asc') == 'desc')
    table = SortableTable(Item.get_sorted_by(sort, reverse),
                          sort_by=sort,
                          sort_reverse=reverse)
    return render_template("home.html", table=table)


@app.route('/search')
def search():
    global res
    items = []
    query_filter = request.args.get('query_filter', default="")
    if not query_filter:
        table = "Not found."
        return render_template("search.html", table=table)
    else:
        for i in range(len(res)):
            keys = [k for k, v in res[i].items() if v == query_filter]
            if keys:
                items.append({'ip_prefix':res[i]['ip_prefix'], 'service':res[i]['service']})
            table = ItemTable(items)
        return render_template("search.html", table=table)


@app.route('/refresh')
def refresh():
    global res
    items = []
    r = requests.get(url)
    ip_list = r.json()["prefixes"]
    service_list = ["S3", "ROUTE53"] 
    res = [d for d in ip_list if d['service'] in service_list]
    for i in range(len(res)):
        items.append(Item(res[i]['ip_prefix'], res[i]['service']))
    return redirect("/")


class Item(object):
    def __init__(self, ip_prefix, service):
        self.ip_prefix = ip_prefix
        self.service = service

    @classmethod
    def get_elements(cls):
        global res
        items = []
        for i in range(len(res)):
            items.append(Item(res[i]['ip_prefix'], res[i]['service']))
        return items

    @classmethod
    def get_sorted_by(cls, sort, reverse=False):
        return sorted(
            cls.get_elements(),
            key=lambda x: getattr(x, sort),
            reverse=reverse)


class ItemTable(Table):
    ip_prefix = Col('IP')
    service = Col('Service')


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')