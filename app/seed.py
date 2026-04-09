import pandas as pd
import sqlite3

conn= sqlite3.connect("fruger.db")
cur= conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS rides (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, time TEXT, booking_id TEXT, booking_status TEXT, customer_ID TEXT, vehicle_type TEXT, pickup_location TEXT, drop_location TEXT, avg_vtat REAL, avg_ctat REAL, cancelled_by_customer INTEGER, cancel_reason_customer TEXT, cancelled_by_driver INTEGER, cancel_reason_driver TEXT, incomplete_rides INTEGER, incomplete_reason TEXT, booking_value REAL, ride_distance REAL, driver_rating REAL, customer_rating REAL, payment_method TEXT)')
df= pd.read_csv('data/ncr_ride_bookings.csv')