# Imports and initiations:
import os
import json
import sys
import requests as requests
import datetime
import time
from manager import mng
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///manager.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

city_frc = []
ask_for = []

# Database update:
try:
    ra_key_file = open('rapidapikey.txt', 'r', encoding='utf-8')
except FileNotFoundError:
    print("Couldn't find file destined for RapidAPI key!.")
    exit()
ra_key = str(ra_key_file.read())
ra_key_file.close()
today = datetime.date.today()

def update_forecasts():
    for dict in mng.locations:
        location = dict
        city = mng.locations[location]
        url = "https://community-open-weather-map.p.rapidapi.com/forecast/daily"
        querystring = {"q": location, "lat": "35", "lon": "139", "cnt": "16", "units": "metric"}
        headers = {
            'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com",
            'x-rapidapi-key': ra_key
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
        filename = city + ".json"    # writing joint raw forecast
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(response.json(), file)
        with open(filename, "r", encoding="utf-8") as forecast_j:
            reader = forecast_j.read()
            forecast_j = json.loads(reader)
            forecast_extract = forecast_j['list']
            for element in forecast_extract:        # daily forecast
                frc_impdate = today
                frc_city = location
                frc_date = element['dt']
                frc_content1 = element['weather'][0]['main']
                frc_content2 = element['weather'][0]['description']
                if frc_content1 == 'Clear':
                    frc_description = "Sunnily"
                if frc_content1 == 'Clouds':
                    if frc_content2 == "few clouds" or frc_content2 == "scattered clouds":
                        frc_description = 'Clouds'
                    else:
                        frc_description = 'Overcast'
                else:
                    frc_description = frc_content1
                frc_temp = element['temp']['day']
                daily_frc = [frc_impdate, frc_city, frc_date, frc_description, frc_temp]
                oper_args = daily_frc
                mng.callbacks['db_put'](oper_args)
                continue
        os.remove(filename)
        time.sleep(7)               # API requirement: max 10 updates/min
        continue
    procedure = "db_clean"
    oper_args = []
    mng.callbacks[procedure](oper_args)

if ra_key:                  # trzeba wpisać swój klucz do pliku, żeby import zadziałał
    update_forecasts()



@app.route("/", methods=["POST", "GET"])
def get_params():
    if request.method == "POST":
        response = dict(request.form)
        date_from = response["date_from"]
        date_to = response["date_to"]
        sunnily = response["sunnily"]
        clouds = response["clouds"]
        overcast = response["overcast"]
        rain = response["rain"]
        snow = response["snow"]
        temp_floor = response["temp_floor"]
        temp_cap = response["temp_cap"]
        print(date_from, date_to)
        print(sunnily, clouds, overcast, rain, snow)
        print(temp_floor, temp_cap)
        procedure = 'find_it'
        date_from = datetime.datetime.strptime('2021-09-05', "%Y-%m-%d")
        date_to = datetime.datetime.strptime('2021-09-10', "%Y-%m-%d")
        oper_args = [date_from, date_to, sunnily, clouds, overcast, rain, snow, temp_floor,
                     temp_cap]
        mng.callbacks[procedure](oper_args)
    return render_template("index.html")

# def get_params():   ### DO WRZUCANIA NA SZTYWNO
#     procedure = 'find_it'
#     date_from = datetime.datetime.strptime('2021-09-05', "%Y-%m-%d")
#     date_to = datetime.datetime.strptime('2021-09-10', "%Y-%m-%d")
#     sunnily = "a"   # "With love:-)"
#     clouds = "b"    # "OK, accepted"
#     overcast = "c"  # "Rather not"
#     rain = "d"      # "I hate it:-("
#     snow = "c"      # "Rather not"
#     temp_floor = 18.0
#     temp_cap = 25.0
#     oper_args = [date_from, date_to, sunnily, clouds, overcast, rain, snow, temp_floor,
#                 temp_cap]
#     mng.callbacks[procedure](oper_args)
#
# get_params()        # będzie wywoływana z formularza

@app.route("/results/", methods=["POST", "GET"])
def put_scores():                       # będzie zwracała wyniki do formularza
    return render_template("results.html", first_place=mng.winners[0],
                           second_place=mng.winners[1], third_place=mng.winners[2],
                           first_forecast=mng.first, second_forecast=mng.second,
                           third_forecast=mng.third)
#     pass