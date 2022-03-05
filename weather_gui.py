from tkinter import *
from tkinter import font

from mysqlx import Session
from database_manager import DataBaseConnector
import aiohttp
import asyncio
import requests
import time
import matplotlib.pyplot as plt

from server_error import ServerError

class WeatherGui:
    weathers= {'Clear': 'Солнечно', 'Rain': 'Дождь', 'Clouds': 'Облачно', 'Snow': 'Снег'}
    appid = "728abff1d97171ab28a008e3e5800944"
    url = "http://api.openweathermap.org/"

    def __init__(self, window):
        self.window = window
        window.title("Погода")
        window.geometry('400x300')
        self.lbl = Label(window, text="Введите город  ")

        self.lbl.grid(column=0, row=0)

        self.lbl2 = Label(window, text="")

        self.lbl2.grid(row=1, columnspan=2, rowspan=4, column=2)

        self.lbl3 = Label(window, text="История поиска:")
        self.lbl3.grid(row=1, column=0)

        self.e1 = Entry(window)

        self.e1.grid(column=1, row=0, columnspan=2)

        self.citybox = Listbox()
        self.citybox.bind('<<ListboxSelect>>', self.onselect)
        self.redraw_list()
        
        self.citybox.grid(row=2, column=0, columnspan=2,rowspan=100)

        self.btn2 = Button(window, text="График изменения", command=self.get_forecast)
        self.btn = Button(window, text="Поиск", command=self.get_content)
        self.btn.grid(column=3, row=0)
        small_font = font.Font(size=6)
        self.btn3 = Button(window, text="Очистить", font=small_font, command=self.clear_storage)
        self.btn3.grid(column=1, row=1)


    def set_err(self, obj, text):
        obj.configure(text=text, foreground="red")

    def get_cities_from_db(self):
        self.db = DataBaseConnector()
        self.cities= self.db.select_all()

    def clear_storage(self):
        self.db.delete_all()
        self.redraw_list()

    def get_forecast(self):
        async def get():
            try:
                async with aiohttp.ClientSession() as session:
                    await self.forecast(session)
            except ServerError:
                return
            except BaseException:
                self.set_err(self.lbl2, "Нет сети")
        loop = asyncio.get_event_loop()
        a1 = loop.create_task(get())
        loop.run_until_complete(a1)

    def get_content(self):
        text = self.e1.get()
        if text == "":
            return
        async def get():
            try:
                async with aiohttp.ClientSession() as session:
                    await self.get_city(session, text)
                    await self.get_weather(session)
            except ServerError:
                return
            except BaseException:
                self.set_err(self.lbl2, "Нет сети")
        loop = asyncio.get_event_loop()
        a1 = loop.create_task(get())
        loop.run_until_complete(a1)


    def insert_city(self):
        self.db.insertRow(self.e1.get(), self.lat, self.lon)
        self.redraw_list()


    def redraw_list(self):
        self.get_cities_from_db()
        self.citybox.delete(0, END)
        for city in self.cities:
            self.citybox.insert(END, city[1])

    async def forecast(self, session):
        params = {'lat':  self.lat, 'lon':  self.lon, 'exclude': 'minutely,daily', 'appid': self.appid}
        async with session.get(self.url + "data/2.5/onecall", params=params) as response:
            if response.status != 200:
                    self.set_err(self.lbl2, 'Ошибка на стороне сервера, мы не виноваты')
                    raise ServerError('error')
            json_encode = await response.json()
            json_decode = json_encode['hourly']
            dates = []
            temp = []
            for hour in json_decode:
                datetime = time. strftime('%d.%m %H:%M', time.localtime(hour['dt']))
                dates.append(datetime)
                temp.append(hour['temp']- 273.15)
            plt.plot(dates, temp, color='red', marker='o')
            plt.title('График погоды на 2 дня', fontsize=14)
            plt.xlabel('Время', fontsize=14)
            plt.ylabel('Температура', fontsize=14)
            plt.xticks(rotation=90, fontsize=6)
            plt.grid(True)
            plt.show()

    async def get_city(self, session, text):
        params = {'q': text, 'limit': 1, 'appid': self.appid}
        async with session.get(self.url + "geo/1.0/direct", params=params) as response:
            if response.status != 200:
                self.set_err(self.lbl2, 'Ошибка на стороне сервера, мы не виноваты')
                raise ServerError('error')
            json_encode = await response.json()
            json_decode = json_encode[0]
            self.lat = json_decode['lat']
            self.lon = json_decode['lon']
            self.insert_city()

    async def get_weather(self, session):
        params = {'lat': self.lat, 'lon': self.lon, 'appid':self.appid}
        async with session.get(self.url + "data/2.5/weather", params=params) as response:
            if response.status != 200:
                self.set_err(self.lbl2, 'Ошибка на стороне сервера, мы не виноваты')
                raise ServerError('error')
            json_decode = await response.json()
            current_weather = self.weathers[json_decode['weather'][0]['main']]
            current_temp = json_decode['main']['temp'] - 273.15
            day_temp = json_decode['main']['temp_max'] - 273.15
            night_temp = json_decode['main']['temp_min'] - 273.15
            self.lbl2.configure(text='Текущая погода:\n %s\n %d\N{DEGREE SIGN}C\nДнем: %d\N{DEGREE SIGN}C, Ночью: %d\N{DEGREE SIGN}C' % (current_weather, current_temp, day_temp, night_temp),
                                foreground="black")
            self.btn2.grid(columnspan=2, column=2, row=5)

    def onselect(self, evt):
        w = evt.widget
        try:
            index = int(w.curselection()[0])
        except:
            return    
        value = w.get(index)
        self.e1.delete(0,END)
        self.e1.insert(0,value)
        self.get_content()


    def __del__(self):
        del self.db   