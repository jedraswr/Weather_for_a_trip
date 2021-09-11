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
locations = {'amsterdam,nl': 'amsterdam'}#,  'athens,gr': 'athens',     # na razie ograniczona lista
#              'berlin,de': 'berlin', 'berne,ch': 'berne', 'bratislava,sk': 'bratislava',
#              'brussels,be': 'brussels', 'bucharest,ro': 'bucharest',
#              'budapest,hu': 'budapest', 'copenhagen,dk': 'copenhagen',
#              'dublin,ie': 'dublin', 'helsinki,fi': 'helsinki', 'lisbon,pt': 'lisbon',
#              'london,gb': 'london', 'madrid,es': 'madrid', 'moscow,ru': 'moscow',
#              'oslo,no': 'oslo', 'paris,fr': 'paris', 'podgorica,me': 'podgorica',
#              'prague,cz': 'prague', 'reykjavik,is': 'reykjavik', 'riga,lv': 'riga',
#              'rome,it': 'rome', 'sofia,bg': 'sofia', 'stockholm,se': 'stockholm',
#              'tallinn,ee': 'tallinn', 'valletta,mt': 'valletta', 'vienna,at': 'vienna',
#              'vilnius,lt': 'vilnius', 'warsaw,pl': 'warsaw', 'zagreb,hr': 'zagreb',
# }
preferences = {"With love:-)": 3, "OK, accepted": 1, "Rather not": -1,
                         "I hate it:-(": -5}

# Management:

class Manager:
    def __init__(self):
        self.callbacks = {}
        self.get_forecasts = []      # dla wyszukanych prognoz
        self.locations = {}
        self.preferences = {}

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

mng.locations = locations
mng.preferences = preferences

# Data base:

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

# Executives:

@mng.set("db_put")          # entry to data base
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

@mng.set("db_clean")        # deleting out-of-date forecasts
def db_clear(oper_args):
    last_update = db.session.query(Updates).filter(Updates.date).first()
    erase = db.session.query(Forecasts).filter(Forecasts.impdate != last_update).delete()
    db.session.add(erase)
    db.session.commit()

@mng.set("find_it")         # searching and scoring
def find_it(oper_args):
    date_start = int(time.mktime(oper_args[0].timetuple()))
    date_end = (oper_args[1]) + datetime.timedelta(hours=23)
    date_end = int(time.mktime(date_end.timetuple()))
    db_query = db.session.query(Forecasts).filter(Forecasts.date >= date_start).\
            filter(Forecasts.date <= date_end).all()
    mng.get_forecasts = db_query
    nr_forec = 0
    for element in db_query:            # searching through forecasts database
        db_city = db_query[nr_forec].city
        db_date = db_query[nr_forec].date
        db_description = db_query[nr_forec].description
        db_temp = db_query[nr_forec].temp
        nr_forec += 1
        if db_temp >= oper_args[7] and db_temp <= oper_args[8]:
            temp_score = 2    # scoring for preferred temp.
        elif db_temp > (oper_args[8] + 8) or db_temp < (oper_args[7] - 8):
            temp_score = -2   # scoring for unwanted temp.
        else:
            temp_score = 0      # scoring for irrelevant temp.
        scoring_clear = mng.preferences[oper_args[2]]  # scorings for different weathers
        scoring_clouds = mng.preferences[oper_args[3]]
        scoring_overcast = mng.preferences[oper_args[4]]
        scoring_rain = mng.preferences[oper_args[5]]
        scoring_snow = mng.preferences[oper_args[6]]
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
        daily_score = temp_score + descr_score
        if db_city not in locations_scoring:    # starting counting scoring for location
            locations_scoring[db_city] = daily_score
        else:
            locations_scoring[db_city] += daily_score
        show_date = str(datetime.date.fromtimestamp(db_date))
        daily_keys = (show_date, db_description, db_temp)
        if db_city not in locations_forecasts:  # collecting forecasts elements for locations
            first_set = [daily_keys]
            locations_forecasts[db_city] = first_set
        else:
            locations_forecasts[db_city].append(daily_keys)
        continue
    sorted_scoring = sorted(locations_scoring.items(), key=lambda kv: kv[1], reverse=True)
    print(sorted_scoring)

