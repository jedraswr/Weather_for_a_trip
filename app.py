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

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weatherforatrip.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

city_frc = []
ask_for = []


# Raw data import:
capitals = [('amsterdam', 'amsterdam,nl'), ('athens', 'athens,gr'),
            ('berlin', 'berlin,de'), ('berne', 'berne,ch'),
            ('bratislava', 'bratislava,sk'), ('brussels', 'brussels,be'),
            ('bucharest', 'bucharest,ro'), ('budapest', 'budapest,hu'),
            ('copenhagen', 'copenhagen,dk'), ('dublin', 'dublin,ie'),
            ('helsinki', 'helsinki,fi'), ('lisbon', 'lisbon,pt'),
            ('london', 'london,gb'), ('madrid', 'madrid,es'),
            ('moscow', 'moscow,ru'), ('oslo', 'oslo,no'), ('paris', 'paris,fr'),
            ('podgorica', 'podgorica,me'), ('prague', 'prague,cz'),
            ('reykjavik', 'reykjavik,is'), ('riga', 'riga,lv'), ('rome', 'rome,it'),
            ('sofia', 'sofia,bg'), ('stockholm', 'stockholm,se'),
            ('tallinn', 'tallinn,ee'), ('valletta', 'valletta,mt'),
            ('vienna', 'vienna,at'), ('vilnius', 'vilnius,lt'),
            ('warsaw', 'warsaw,pl'), ('zagreb', 'zagreb,hr')
]
ra_key_file = open('rapidapikey.txt', 'r', encoding='utf-8')
ra_key = str(ra_key_file.read())
ra_key_file.close()
today = datetime.date.today()

def update_forecasts():
    for element in capitals:            # for a location
        city, location = element[0], element[1]
        url = "https://community-open-weather-map.p.rapidapi.com/forecast/daily"
        querystring = {"q": location, "lat": "35", "lon": "139", "cnt": "16", "units": "metric"}
        headers = {
            'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com",
            'x-rapidapi-key': ra_key
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
        filename = "forecasts/" + city + ".json"    # writing joint raw forecast
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(response.json(), file)
        forecast_j = open(filename, "r", encoding="utf-8")
        reader = forecast_j.read()
        forecast_j.close()
        forecast_j = json.loads(reader)
        forecast_extract = forecast_j['list']
        for element in forecast_extract:        # daily forecast
            frc_impdate = today
            frc_city = location
            frc_date = element['dt'] ### - 691200
            frc_content1 = element['weather'][0]['main']
            frc_content2 = element['weather'][0]['description']
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
            mng.callbacks['db_put'](oper_args)      #dopisać funkcję kasującą .json
            continue
        time.sleep(7)
        continue

# update_forecasts()

def get_params():           #będzie pobranie z formularza, na razie na sztywno
    procedure = 'find_it'
    date_from = datetime.datetime.strptime('2021-09-05', "%Y-%m-%d" )
    date_to = datetime.datetime.strptime('2021-09-08', "%Y-%m-%d")
    Clear = "With love:-)"
    Clouds = "OK, accepted"
    Overcast = "Rather not"
    Rain = "I hate it:-("
    Snow = "Rather not"
    temp_floor = 18.0
    temp_cap = 25.0
    oper_args = [date_from, date_to, Clear, Clouds, Overcast, Rain, Snow, temp_floor,
                temp_cap]
    mng.callbacks[procedure](oper_args)

get_params()
