# Imports and initiations:
import os
import json
import sys
import requests as requests
import datetime
import time
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///manager.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

locations_scoring = {}
locations_forecasts = {}

class Manager:
    def __init__(self):
        self.callbacks = {}
        self.get_forecasts = []      # dla wyszukanych prognoz
        self.params = []            # dla parametrów wyszukiwania z formularza

    def set(self, procedure):
        def decorate(callback):
            self.callbacks[procedure] = callback
        return decorate

    def do_this(self, procedure, oper_args):
        if procedure in self.callbacks:
            self.callbacks[procedure](oper_args)
        else:
            warning_msg = ("No such procedure!")
        return warning_msg

mng = Manager()

class Forecasts(db.Model):
    pk = db.Column(db.Integer, primary_key=True)
    impdate = db.Column(db.Date, nullable=False, unique=False)
    city = db.Column(db.String(30), nullable=False, unique=False)
    date = db.Column(db.Integer, nullable=False, unique=False)
    description = db.Column(db.String(10), nullable=False, unique=False)
    temp = db.Column(db.Float, nullable=False, unique=False)

class Updates(db.Model):
    note = db.Column(db.String, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=False)

db.create_all()
# db.session.query(Forecasts).delete()
# db.session.query(Updates).delete()
# db.session.query(Forecasts).filter(Forecasts.pk>17).delete()


@mng.set("db_put")
def db_put(oper_args):
    db_frc_entry = Forecasts(impdate=oper_args[0], city=oper_args[1], date=oper_args[2],
                                 description=oper_args[3], temp=oper_args[4])
    db.session.add(db_frc_entry)
    if_update = db.session.query(Updates).filter(Updates.note == 'last_update').first()
    if not if_update:
        db_upd_entry = Updates(note='last_update', date=oper_args[0])
        db.session.add(db_upd_entry)
    else:
        if_update.date = oper_args[0]
    db.session.commit()

@mng.set("find_it")
def db_get(oper_args):
    date_start = int(time.mktime(oper_args[0].timetuple()))
    date_end = (oper_args[1]) + datetime.timedelta(hours=23)
    date_end = int(time.mktime(date_end.timetuple()))
    print(date_start)
    print(date_end)
    # date_start = 1631224800 - (2 * 24 * 60 * 60)    # 2021-09-08
    # date_end = 1631224800                           # 2021-09-10
    db_query = db.session.query(Forecasts).filter(Forecasts.date >= date_start).\
            filter(Forecasts.date <= date_end).all()
    mng.get_forecasts = db_query
    # print(db_query)                     # Na razie ma wydrukować jakąś postać
    nr_forec = len(db_query)
    print(nr_forec)
    nr_forec = 0
    for element in db_query:
        db_city = db_query[nr_forec].city
        db_date = db_query[nr_forec].date
        db_description = db_query[nr_forec].description
        db_temp = db_query[nr_forec].temp
        nr_forec += 1
        if db_temp >= oper_args[7] and db_temp <= oper_args[8]:
            temp_score = 2
        elif db_temp > (oper_args[8] + 8) or db_temp < (oper_args[7] - 8):
            temp_score = -2
        else:
            temp_score = 0
        # print(temp_score)
        scoring_table = {"With love:-)": 3, "OK, accepted": 1, "Rather not": -1,
                         "I hate it:-(": -5}
        scoring_clear = scoring_table[oper_args[2]]
        scoring_clouds = scoring_table[oper_args[3]]
        scoring_overcast = scoring_table[oper_args[4]]
        scoring_rain = scoring_table[oper_args[5]]
        scoring_snow = scoring_table[oper_args[6]]
        if db_description == "Clear":
            descr_score = scoring_clear
        if db_description == "Clouds":
            descr_score = scoring_clouds
        if db_description == "Overcast":
            descr_score = scoring_overcast
        if db_description == "Rain":
            descr_score = scoring_rain
        if db_description == "Snow":
            descr_score = scoring_snow
        # print(descr_score)
        daily_score = temp_score + descr_score
        # print(db_city, daily_score)
        if db_city not in locations_scoring:
            locations_scoring[db_city] = daily_score
        else:
            locations_scoring[db_city] += daily_score
        show_date = str(datetime.date.fromtimestamp(db_date))
        # show_date = datetime.datetime.strptime(show_date, "%Y-%m-%d")
        daily_keys = (show_date, db_description, db_temp)
        if db_city not in locations_forecasts:
            first_set = [daily_keys]
            locations_forecasts[db_city] = first_set
        else:
            locations_forecasts[db_city].append(daily_keys)
        continue
    print(locations_scoring)
    print(locations_forecasts)
    sorted_scoring = sorted(locations_scoring.items(), key=lambda kv: kv[1], reverse=True)
    print(sorted_scoring)

