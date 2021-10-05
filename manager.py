# Imports and initiations:
import datetime
import time
from flask import Flask
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
preferences = {"With love:-)": 10, "OK, accepted": 3, "Rather not": -3, "I hate it:-(": -10}     #scoring for weather types

col_dt = []
col_sky = []
col_temp = []

# Management:

class Manager:
    def __init__(self):
        self.callbacks = {}
        self.locations = {}
        self.preferences = {}
        self.first = {}
        self.second = {}
        self.third = {}
        self.winners = []
        self.warning_msg = ""
        self.data_range = ""

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

@mng.set("find_it")         # searching and scoring forecasts
def find_it(oper_args):
    date_start = int(time.mktime(oper_args[0].timetuple()))
    date_end = (oper_args[1]) + datetime.timedelta(hours=23)
    date_end = int(time.mktime(date_end.timetuple()))
    db_query = db.session.query(Forecasts).filter(Forecasts.date >= date_start).\
            filter(Forecasts.date <= date_end).all()
    locations_forecasts.clear()
    nr_forec = 0
    for element in db_query:            # searching through forecasts database
        db_city = db_query[nr_forec].city
        db_date = db_query[nr_forec].date
        db_description = db_query[nr_forec].description
        db_temp = db_query[nr_forec].temp
        nr_forec += 1
        if db_temp >= float(oper_args[7]) and db_temp <= float(oper_args[8]):
            temp_score = 5          # scoring for preferred temp.
        elif db_temp > (float(oper_args[8]) + 7) or db_temp < (float(oper_args[7]) - 7):
            temp_score = -5         # scoring for unwanted temp.
        else:
            temp_score = 0          # scoring for irrelevant temp.
        scoring_sunnily = mng.preferences[oper_args[2]]  # scorings for different weathers
        scoring_clouds = mng.preferences[oper_args[3]]
        scoring_overcast = mng.preferences[oper_args[4]]
        scoring_rain = mng.preferences[oper_args[5]]
        scoring_snow = mng.preferences[oper_args[6]]
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
        continue
    sorted_scoring = sorted(locations_scoring.items(), key=lambda kv: kv[1], reverse=True)
    city1 = sorted_scoring[0][0]        # scorings collection for presentation
    city2 = sorted_scoring[1][0]
    city3 = sorted_scoring[2][0]
    mng.winners.clear()
    mng.winners.append(mng.locations[city1])
    mng.winners.append(mng.locations[city2])
    mng.winners.append(mng.locations[city3])
    mng.first.clear()
    mng.second.clear()
    mng.third.clear()
    procedure = "load_forecasts"
    oper_args = [1, locations_forecasts[city1]]
    mng.callbacks[procedure](oper_args)
    oper_args = [2, locations_forecasts[city2]]
    mng.callbacks[procedure](oper_args)
    oper_args = [3, locations_forecasts[city3]]
    mng.callbacks[procedure](oper_args)

@mng.set("load_forecasts")
def load_forecasts(oper_args):
    nr = oper_args[0]
    for element in oper_args[1]:
        comp_dt = element[0] + ","
        comp_sky = str(element[1])
        comp_tmp = str(round(element[2],1)) + " C"
        comp_skytmp = "  " + comp_sky + ",  " + comp_tmp
        if nr == 1:
            mng.first[comp_dt] = comp_skytmp
        if nr == 2:
            mng.second[comp_dt] = comp_skytmp
        if nr == 3:
            mng.third[comp_dt] = comp_skytmp
