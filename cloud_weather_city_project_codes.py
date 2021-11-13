import requests
import re
import json
import sys
import json
import websocket

# ---------------------------------
user = "your user name"
pw = "your pw"
project_id = "your project"
# ---------------------------------
var_city = "City_cv"
var_weather = "Weather_cv"
var_description = "Description_cv"
var_temperature = "Temprature_cv"
var_temperature_min = "Temprature Min_cv"
var_temperature_max = "Temprature Max_cv"
var_error = "Error_cv"
var_date = "Date_cv"
# --------------------------------------
api_key = "your api key"

ws = websocket.WebSocket()

#self.chars = "abcdefghijklmnopqrstuvwxyz0123456789+-. _"
chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890@-_> ?%#^/+=}{().,:;|½  <é   "


def encode(text_data):

    text = str(text_data)

    try:
        encoded = ""
        length = int(len(text))
        for i in range(0, length):
            try:
                x = int(chars.index(text[i])+int(11))
                encoded = encoded + str(x)
            except ValueError:
                print('Character not supported')
        return encoded
    except:
        return "74"


def decode(text):

    try:
        decoded = ""
        y = 0
        for i in range(0, len(text)//2):
            x = chars[int(str(text[y])+str(text[int(y)+1]))-11]
            decoded = str(decoded)+str(x)
            y += 2
        return decoded

    except:
        return "error"


def city_weather(city_name):

    link = "http://api.openweathermap.org/data/2.5/weather?q=" + \
        str(city_name)+"&units=metric&APPID="+api_key

    response = requests.get(link)

    try:
        json_data = response.json()

        weather_data_dic = {
            "city": city_name,
            "weather": json_data["weather"][0]["main"],
            "description": json_data["weather"][0]["description"],
            "temprature": str((json_data["main"]["temp"])),
            "temprature_min": str((json_data["main"]["temp_min"])),
            "temprature_max": str((json_data["main"]["temp_max"])),
            "error": "-"
        }

        return weather_data_dic
    except:
        weather_data_dic = {
            "city": "-",
            "weather": "-",
            "description": "-",
            "temprature": "-",
            "temprature_min": "-",
            "temprature_max": "-",
            "error": "City not found"
        }
        return weather_data_dic


def encode_weather(weather_data_dic):
    weather_data_dic_encode = {

        "city": encode(weather_data_dic["city"]),
        "weather": encode(weather_data_dic["weather"]),
        "description": encode(weather_data_dic["description"]),
        "temprature": encode(weather_data_dic["temprature"]),
        "temprature_min": encode(weather_data_dic["temprature_min"]),
        "temprature_max": encode(weather_data_dic["temprature_max"]),
        "error": encode(weather_data_dic["error"]),
    }
    return weather_data_dic_encode


def set_cloud_var(username, project_id, variable, value, sessionId):
    try:
        ws.send(json.dumps({
            'method': 'set',
            'name': '☁ ' + variable,
            'value': str(value),
            'user': username,
            'project_id': project_id
        }) + '\n')
    except BrokenPipeError:

        ws.connect('wss://clouddata.scratch.mit.edu', cookie='scratchsessionsid='+sessionId+';',
                   origin='https://scratch.mit.edu', enable_multithread=True)
        ws.send(json.dumps({
            'method': 'handshake',
            'user': username,
            'project_id': project_id
        }) + '\n')

        ws.send(json.dumps({
            'method': 'set',
            'name': '☁ ' + variable,
            'value': str(value),
            'user': username,
            'project_id': project_id
        }) + '\n')


def login_scratch(username, password):

    headers = {
        "x-csrftoken": "a",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": "scratchcsrftoken=a;scratchlanguage=en;",
        "referer": "https://scratch.mit.edu",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
    }
    try:
        data = json.dumps({
            "username": username,
            "password": password
        })
        request = requests.post(
            'https://scratch.mit.edu/login/', data=data, headers=headers)

        sessionId = re.search(
            '\"(.*)\"', request.headers['Set-Cookie']).group()

        print(sessionId)

        token = request.json()[0]["token"]

        headers = {
            "x-requested-with": "XMLHttpRequest",
            "Cookie": "scratchlanguage=en;permissions=%7B%7D;",
            "referer": "https://scratch.mit.edu",
        }
        request = requests.get(
            "https://scratch.mit.edu/csrf_token/", headers=headers)
        csrftoken = re.search(
            "scratchcsrftoken=(.*?);", request.headers["Set-Cookie"]
        ).group(1)

    except AttributeError:
        sys.exit('Error: Invalid credentials. Authentication failed.')
    else:
        headers = {
            "x-csrftoken": csrftoken,
            "X-Token": token,
            "x-requested-with": "XMLHttpRequest",
            "Cookie": "scratchcsrftoken="
            + csrftoken
            + ";scratchlanguage=en;scratchsessionsid="
            + sessionId
            + ";",
            "referer": "",
        }

    return sessionId


def scratch_websocket_connection(d_username, d_pid):

    # Scratch login
    d_sessionId = login_scratch(user, pw)

    ws.connect('wss://clouddata.scratch.mit.edu', cookie='scratchsessionsid='+d_sessionId+';',
               origin='https://scratch.mit.edu', enable_multithread=True)

    ws.send(json.dumps({
        'method': 'handshake',
        'user': d_username,
        'project_id': str(d_pid)
    }) + '\n')

    # Infinite loop waiting for WebSocket data
    while True:
        txt = ws.recv()

        x = txt.splitlines()

        for i in x:

            y = json.loads(i)

            name = y["name"]
            city = y["value"]
            city_encoded = decode(city)
            city_lower = city_encoded.lower()

            city_var = '☁ ' + var_city

            if name == city_var:

                city_weather_dic = city_weather(city_lower)
                city_weather_encode_dic = encode_weather(city_weather_dic)

                set_cloud_var(user, project_id, var_weather,
                              city_weather_encode_dic["weather"], d_sessionId)
                set_cloud_var(user, project_id, var_description,
                              city_weather_encode_dic["description"], d_sessionId)
                set_cloud_var(user, project_id, var_temperature,
                              city_weather_encode_dic["temprature"], d_sessionId)
                set_cloud_var(user, project_id, var_temperature_min,
                              city_weather_encode_dic["temprature_min"], d_sessionId)
                set_cloud_var(user, project_id, var_temperature_max,
                              city_weather_encode_dic["temprature_max"], d_sessionId)
                set_cloud_var(user, project_id, var_error,
                              city_weather_encode_dic["error"], d_sessionId)


scratch_websocket_connection(user, project_id)
