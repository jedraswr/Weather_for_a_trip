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

class Manager:
    def __init__(self):
        self.callbacks = {}
        self.imp_forecast = []
        self.params = []

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

# db.session.query(Forecasts).delete()
# db.session.query(Updates).delete()
# db.session.query(Forecasts).filter(Forecasts.pk>17).delete()
db.create_all()


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

@mng.set("db_get")
def db_get(oper_args):
    date_st = int(time.mktime(oper_args[0].timetuple()))
    date_end = int(time.mktime(oper_args[0].timetuple()))
    print("dates")
    print(date_st)
    print(date_end)
    # db.session.query(Manager).filter(Forecasts.date <= )






@mng.set("find_it")
def scoring():
    db_description = "Clouds"
    db_temp = 21.2
    db_Forecasts_description = db_description
    db_Forecasts_temp = db_temp
    ask_for = ['2021-09-05', '2021-09-12', 'With love:-)', 'OK, accepted', 'Rather not', 'I hate it:-(', 'Rather not', 18.0, 25.0]
    if db_Forecasts_temp >= ask_for[7] and db_Forecasts_temp <= ask_for[8]:
        temp_score = 2
    elif db_Forecasts_temp > (ask_for[8] + 8) or db_Forecasts_temp < (ask_for[7] - 8):
        temp_score = -2
    else:
        temp_score = 0
    # print(temp_score)
    scoring_table = {"With love:-)": 3, "OK, accepted": 1, "Rather not": -1,
                     "I hate it:-(": -5}
    scoring_clear = scoring_table[ask_for[2]]
    # print(scoring_clear)
    scoring_clouds = scoring_table[ask_for[3]]
    # print(scoring_clouds)
    scoring_overcast = scoring_table[ask_for[4]]
    # print(scoring_overcast)
    scoring_rain = scoring_table[ask_for[5]]
    # print(scoring_rain)
    scoring_snow = scoring_table[ask_for[6]]
    # print(scoring_snow)
    if db_Forecasts_description == "Clear":
        descr_score = scoring_clear
    if db_Forecasts_description == "Clouds":
        descr_score = scoring_clouds
    if db_Forecasts_description == "Overcoast":
        descr_score = scoring_overcast
    if db_Forecasts_description == "Rain":
        descr_score = scoring_rain
    if db_Forecasts_description == "Snow":
        descr_score = scoring_snow
    # print(descr_score)
    daily_score = temp_score + descr_score
    # print(daily_score)



