import sqlite3

conn = sqlite3.connect('horoscope.db')

c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS hero(
        id INTEGER  PRIMARY KEY    NOT NULL,
        name                TEXT   NOT NULL
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS team(
	id INT   PRIMARY KEY     NOT NULL,
	name             TEXT    NOT NULL 
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS player(
	id INTEGER  PRIMARY KEY    NOT NULL
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS match(
	id INTEGER  PRIMARY KEY    NOT NULL,
	radiant_win       CHAR(1)  NOT NULL,
	radiant_team_id     INT    NOT NULL,
	dire_team_id        INT    NOT NULL,
	start_time          INT    NOT NULL,
	FOREIGN KEY(radiant_team_id) REFERENCES team(id),
	FOREIGN KEY(dire_team_id) REFERENCES team(id)
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS playermatch(
	id INTEGER   PRIMARY KEY AUTOINCREMENT,
	player_id        INT      NOT NULL,
	match_id         INT      NOT NULL,
	team_id          INT      NOT NULL,
	hero_id          INT      NOT NULL,
	kills            INT,
	deaths           INT,
	assists          INT,
	gold             INT,
	last_hits        INT,
	denies           INT,
	gpm              INT,
	xpm              INT,
	gold_spent       INT,
	hero_damage      INT,
	tower_damage     INT,
	hero_healing     INT,
	level            INT,
	FOREIGN KEY(player_id) REFERENCES player(id),
	FOREIGN KEY(match_id)  REFERENCES match(id),
	FOREIGN KEY(team_id)   REFERENCES team(id)
)''')

conn.commit()

conn.close()
