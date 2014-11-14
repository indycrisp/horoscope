import sqlite3

conn = sqlite3.connect('horoscope.db')
c = conn.cursor()

c.execute('''
select
	hero.id,
	hero.name,
	avg(kills) kills,
	avg(deaths) deaths,
	avg(assists) assists,
	avg(last_hits) last_hits,
	avg(denies) denies,
	avg(gpm) gpm,
	avg(xpm) xpm,
	avg(hero_damage) hero_damage,
	avg(tower_damage) tower_damage,
	avg(hero_healing) hero_healing
from
	hero,
	playermatch
where
	hero.id = playermatch.hero_id
group by
	hero.id,
	hero.name
''')

avg_rows = c.fetchall()

c.execute('''
select
	player.id,
	hero.name,
	count(playermatch.match_id) num_matches,
        avg(kills) kills,
        avg(deaths) deaths,
        avg(assists) assists,
        avg(last_hits) last_hits,
        avg(denies) denies,
        avg(gpm) gpm,
        avg(xpm) xpm,
        avg(hero_damage) hero_damage,
        avg(tower_damage) tower_damage,
        avg(hero_healing) hero_healing
from
	player,
	playermatch,
	hero
where
	player.id = playermatch.player_id
	and playermatch.hero_id = hero.id
group by
	player.id,
	hero.name
''')

player_rows = c.fetchall()

# collect averages into a map of hero -> stat -> average value
cols = ['kills', 'deaths', 'assists', 'last_hits', 'denies', 'gpm', 'xpm', 'hero_damage', 'tower_damage', 'hero_healing']
avgs = {}
for row_tuple in avg_rows:
	row = list(row_tuple)
	account_id = row.pop(0)
	hero_name  = row.pop(0)
	avgs[hero_name] = {}
	for i in range(len(cols)):
		avgs[hero_name][cols[i]] = row[i]

player_vals = {}
for row_tuple in player_rows:
	row = list(row_tuple)
	account_id = row.pop(0)
	hero_name = row.pop(0)
	num_matches = row.pop(0)

	if account_id not in player_vals: player_vals[account_id] = {}
	if hero_name not in player_vals[account_id]: player_vals[account_id][hero_name] = {}

	for i in range(len(cols)):
		player_vals[account_id][hero_name][cols[i]] = row[i]

print(str(player_vals))
