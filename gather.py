import requests
import json
import sqlite3

STEAM_KEY = '5D95A220441B79EDA8540E98E670082E'
STEAM_BASE_URL = 'https://api.steampowered.com/IDOTA2Match_570/'
MIN_LEAGUE_ID = 1936

hero_rows = []
match_rows = []
player_rows = []
playermatch_rows = []
team_rows = []

# get hero data
print("getting heroes...")
heroes_response = requests.get('https://api.steampowered.com/IEconDOTA2_570/GetHeroes/V001/?key=' + STEAM_KEY)
print("done")

heroes = heroes_response.json()['result']['heroes']
for hero in heroes:
	hero_rows.append(
		(
			hero['id'],
			hero['name']
		)
	)

# get league ids
print("getting leagues...")
leagues_response = requests.get(STEAM_BASE_URL + 'GetLeagueListing/V001/?key=' + STEAM_KEY)
print("done")

# get match ids from each league
match_radiantid = {}
match_direid = {}
match_start_time = {}
match_ids = []
team_ids = []
league_count = 1
league_ids = [1936, 104, 1350, 1886, 1942, 1761, 1887, 1663, 1803, 1709, 2190, 2032, 2013, 2045, 2096]
for league_id in league_ids:
	print("getting matches for league " + str(league_count) + "/" + str(len(league_ids)), end="\r")
	matches_response = requests.get(STEAM_BASE_URL + 'GetMatchHistory/V001/' + '?league_id=' + str(league_id) + '&key=' + STEAM_KEY)

	matches = matches_response.json()['result']['matches']
	for match in matches:
		if match['dire_team_id'] > 0 and match['radiant_team_id'] > 0:
			match_id = match['match_id']
			match_ids.append(match_id)
			match_radiantid[match_id] = match['radiant_team_id']
			match_direid[match_id] = match['dire_team_id']
			team_ids.append(match['radiant_team_id'])
			team_ids.append(match['dire_team_id'])
			match_start_time[match_id] = match['start_time']

	league_count += 1

print ("done matches")

# get team data
unique_team_ids = list(set(team_ids))

team_count = 1
for team_id in unique_team_ids:
	print("getting team " + str(team_count) + "/" + str(len(unique_team_ids)), end="\r")
	team_response = requests.get(STEAM_BASE_URL + 'GetTeamInfoByTeamID/V001/?start_at_team_id=' + str(team_id) + '&teams_requested=' + str(1) + '&key=' + STEAM_KEY)

	teams = team_response.json()['result']
	for team in teams['teams']:
		team_rows.append(
			(
				team_id,
				team['name']
			)
		)

	team_count += 1
	

print("done teams")

# get match details for each match id
seen_players = {}
match_count = 1
for match_id in match_ids:
	print("getting match details for match " + str(match_count) + "/" + str(len(match_ids)), end="\r")	
	match_response = requests.get(STEAM_BASE_URL + 'GetMatchDetails/V001/' + '?match_id=' + str(match_id) + '&key=' + STEAM_KEY)

	# match data
	match = match_response.json()['result']
	match_rows.append(
		(
			match_id,
			'Y' if match['radiant_win'] else 'N',
			match_radiantid[match_id],
			match_direid[match_id],
			match_start_time[match_id]
		)
	)

	# player and playermatch data
	for player in match['players']:
		team_id = 0
		if player['player_slot'] > 4:
			team_id = match_direid[match_id]
		else:
			team_id = match_radiantid[match_id]

		if player['account_id'] not in seen_players.keys():
			player_rows.append([player['account_id']])
			seen_players[player['account_id']] = 1
	
	
		playermatch_rows.append(
			(
				player['account_id'],
				match_id,
				team_id,
				player['hero_id'],
				player['kills'],
				player['deaths'],
				player['assists'],
				player['gold'],
				player['last_hits'],
				player['denies'],
				player['gold_per_min'],
				player['xp_per_min'],
				player['gold_spent'],
				player['hero_damage'],
				player['tower_damage'],
				player['hero_healing'],
				player['level']
			)
		)
	
	match_count += 1

print("done matches")

# DB transaction
conn = sqlite3.connect('horoscope.db')
c = conn.cursor()

print("deleting existing data...")
c.execute('''DELETE FROM hero''')
c.execute('''DELETE FROM team''')
c.execute('''DELETE FROM match''')
c.execute('''DELETE FROM player''')
c.execute('''DELETE FROM playermatch''');
print("done")

print("writing new data...")
c.executemany('''
INSERT INTO hero
        (id, name)
VALUES
        (?,?)
''', hero_rows)
c.executemany('''
INSERT INTO team
	(id, name)
VALUES
	(?,?)
''', team_rows)

c.executemany('''
INSERT INTO match 
	(id, radiant_win, radiant_team_id, dire_team_id, start_time)
VALUES
	(?,?,?,?,?)
''', match_rows)

#TODO: get player name
c.executemany('''
INSERT INTO player 
	(id)
VALUES
	(?)
''', player_rows)

c.executemany('''
INSERT INTO playermatch
	(id, player_id, match_id, team_id, hero_id, kills, deaths, assists, gold, last_hits, denies, gpm, xpm, gold_spent, hero_damage, tower_damage, hero_healing, level)
VALUES
	(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
''', playermatch_rows)

print("done")
conn.commit()
conn.close()
