import sqlite3

conn = sqlite3.connect('horoscope.db')

c = conn.cursor()

c.execute('''DROP TABLE IF EXISTS player''')
c.execute('''DROP TABLE IF EXISTS match''')
c.execute('''DROP TABLE IF EXISTS playermatch''')
c.execute('''DROP TABLE IF EXISTS team''')

conn.commit()

conn.close()
