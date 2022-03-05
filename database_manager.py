
import sqlite3

class DataBaseConnector:
    def __init__(self):
        try:
            self.sqlite_connection = sqlite3.connect('weather.db')

        except sqlite3.Error as error:
            print("Ошибка при подключении к sqlite", error)

    def __del__(self):
        if(self.sqlite_connection):
            self.sqlite_connection.close()

    def select_all(self):
        cursor = self.sqlite_connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS city(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, lat DOUBLE NOT NULL, lon DOUBLE NOT NULL)")
        cursor.execute("select * from city order by id desc limit 10")
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def insertRow(self, city_name, lat, lon):
        cursor = self.sqlite_connection.cursor()
        sql = 'INSERT INTO city(name, lat, lon) VALUES (?, ?, ?)'
        cursor.execute(sql, (city_name, lat, lon))
        self.sqlite_connection.commit()
        cursor.close()

    def delete_all(self):
        cursor = self.sqlite_connection.cursor()
        sql = 'DELETE FROM city'
        cursor.execute(sql)
        self.sqlite_connection.commit()
        cursor.close()