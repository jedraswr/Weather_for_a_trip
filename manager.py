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
locations = {'amsterdam,nl': 'Amsterdam',  'athens,gr': 'Athens',
             'berlin,de': 'Berlin', 'berne,ch': 'Berne', 'bratislava,sk': 'Bratislava',
             'brussels,be': 'Brussels', 'bucharest,ro': 'Bucharest',
             'budapest,hu': 'Budapest', 'copenhagen,dk': 'Copenhagen',
             'dublin,ie': 'Dublin', 'helsinki,fi': 'Helsinki', 'lisbon,pt': 'Lisbon',
             'london,gb': 'London', 'madrid,es': 'Madrid', 'moscow,ru': 'Moscow',
             'oslo,no': 'Oslo', 'paris,fr': 'Paris', 'podgorica,me': 'Podgorica',
             'prague,cz': 'Prague', 'reykjavik,is': 'Reykjavik', 'riga,lv': 'Riga',
             'rome,it': 'Rome', 'sofia,bg': 'Sofia', 'stockholm,se': 'Stockholm',
             'tallinn,ee': 'Tallinn', 'valletta,mt': 'Valletta', 'vienna,at': 'Vienna',
             'vilnius,lt': 'Vilnius', 'warsaw,pl': 'Warsaw', 'zagreb,hr': 'Zagreb',
}
preferences = {"With love:-)": 5, "OK, accepted": 1, "Rather not": -1, "I hate it:-(": -3}     #scoring for weather types

first = []
second = []
third = []
col_dt = []
col_sky = []
col_temp = []

# Management:

class Manager:
    def __init__(self):
        self.callbacks = {}
        self.get_forecasts = []      # dla wyszukanych prognoz
        self.locations = {}
        self.preferences = {}
        self.chosen_frc = []
        self.first = []
        self.second = []
        self.third = []
        self.winners = []

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
def db_clean(oper_args):
    find_row = db.session.query(Updates).filter(Updates.note == "last_update").first()
    last_update = find_row.date     # powinien zwrócić datę z find_row
    db.session.query(Forecasts).filter(Forecasts.impdate != last_update).delete()
    db.session.commit()

def format_data():   ### wersja na 3 kolumny
    nrf = 1
    for element in mng.chosen_frc:
        for component in element:
            comp_dt = component[0]
            comp_sky = str(component[1])
            # print(comp_sky)
            comp_tmp = str(component[2]) + " C"
            daily_frc = [comp_dt, comp_sky, comp_tmp]
            if nrf == 1:
                first.append(daily_frc)
            elif nrf == 2:
                second.append(daily_frc)
            else:
                third.append(daily_frc)
            continue
        if nrf == 1:
            mng.first = first
        elif nrf == 2:
            mng.second = second
        else:
            mng.third = third
        nrf += 1
        continue
    # print(mng.first)
    # print(mng.second)
    # print(mng.third)

# def format_data(): ### wersja na 9 kolumn - do poprawienia
#     nrf = 1
#     for element in mng.chosen_frc:
#         for component in element:
#             col_dt.append(component[0])
#             col_sky.append(component[1])
#             col_temp.append(str(component[2]) + " C")
#             continue
#         # print(col_dt)
#         # print(col_sky)
#         # print(col_temp)
#         if nrf == 1:
#             mng.first.append(col_dt)
#             mng.first.append(col_sky)
#             mng.first.append(col_temp)
#             # print(mng.first)
#         elif nrf == 2:
#             mng.second.append(col_dt)
#             mng.second.append(col_sky)
#             mng.second.append(col_temp)
#             # print(mng.second)
#         else:
#             mng.third.append(col_dt)
#             mng.third.append(col_sky)
#             mng.third.append(col_temp)
#             # print(mng.third)
#         nrf += 1
#         print(mng.first)
#         print(mng.second)
#         print(mng.third)
#         continue


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
        if db_temp >= float(oper_args[7]) and db_temp <= float(oper_args[8]):
            temp_score = 2          # scoring for preferred temp.
        elif db_temp > (float(oper_args[8]) + 8) or db_temp < (float(oper_args[7]) - 8):
            temp_score = -2         # scoring for unwanted temp.
        else:
            temp_score = 0      # scoring for irrelevant temp.
        scoring_sunnily = mng.preferences[oper_args[2]]  # scorings for different weathers
        scoring_clouds = mng.preferences[oper_args[3]]
        scoring_overcast = mng.preferences[oper_args[4]]
        scoring_rain = mng.preferences[oper_args[5]]
        scoring_snow = mng.preferences[oper_args[6]]
        # print(mng.preferences)
        if db_description == "Sunnily":
            descr_score = scoring_sunnily
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
        # print(locations_forecasts)
        continue
    sorted_scoring = sorted(locations_scoring.items(), key=lambda kv: kv[1], reverse=True)
    # print(sorted_scoring)
    city1 = sorted_scoring[0][0]
    city2 = sorted_scoring[1][0]
    city3 = sorted_scoring[2][0]
    forecast1 = locations_forecasts[city1]
    forecast2 = locations_forecasts[city2]
    forecast3 = locations_forecasts[city3]
    mng.chosen_frc.append(forecast1)
    mng.chosen_frc.append(forecast2)
    mng.chosen_frc.append(forecast3)
    mng.winners.append(mng.locations[city1])
    mng.winners.append(mng.locations[city2])
    mng.winners.append(mng.locations[city3])
    # print(mng.winners)
    format_data()
