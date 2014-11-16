import sqlite3
import numpy
from sklearn.naive_bayes import GaussianNB

conn = sqlite3.connect('horoscope.db')
c = conn.cursor()

# Use SQL to get the mean/std deviation with the query below

#SELECT ID, AVG(diff) AS average,
#       AVG(diff*diff) - AVG(diff)*AVG(diff) AS variance,
#       SQRT(AVG(diff*diff) - AVG(diff)*AVG(diff)) AS stdev

# Then use these values in a bayes calculation, see naive
# bayes classifier on wiki
c.execute('''
select
	case
		when
			(
				team.id = match.radiant_team_id
				and match.radiant_win = 'Y' 
			)
			or (
				team.id = match.dire_team_id
				and match.radiant_win = 'N'
			) then
				1
		else
			0
	end as win,
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
	match,
	team,
	player,
	playermatch
where
	match.id = playermatch.match_id
	and team.id = player.team_id
	and playermatch.player_id = player.id
group by
	match.id,
	team.id,
	win
order by
	match.id
''')

rows = c.fetchall()

#TODO: don't select max team, players might have switched teams
c.execute('''
select
	playermatch.player_id,
	max(player.team_id) team_id,
	count(playermatch.id) matches_played,
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
	playermatch,
	player
where
	playermatch.player_id = player.id
group by
	playermatch.player_id
order by
	player_id,
	team_id,
	matches_played
''')

player_rows = c.fetchall()
c.close()

# build the classifier
# game_stats is a list of lists representing feature vectors
# results is a list like [0, 1, 1, 0] where 0s are losses and 1s are wins
game_stats = []
results = []

for row_tuple in rows:
	row = list(row_tuple)
	win = row.pop(0)
	results.append(win)
	game_stats.append(row)

np_results = numpy.array(results)
np_game_stats = numpy.array(game_stats)

classifier = GaussianNB()
classifier.fit(np_game_stats, np_results)

# how good is the classifier?
print('Classifier accuracy: ' + str(classifier.score(np_game_stats, np_results)))

# get number of games played by each player for each team
games_played = {}
for player_tuple in player_rows:
	player = list(player_tuple)
	if player[0] not in games_played.keys(): games_played[player[0]] = {}
	if player[1] not in games_played[player[0]].keys(): games_played[player[0]][player[1]] = 0
	games_played[player[0]][player[1]] = player[2]

print(str(games_played))	
# test EG vs C9
test_team_1 = []
test_team_2 = []
for player_tuple in player_rows:
	player = list(player_tuple)
	for i in range(games_played[player[0]][player[1]]):
		if player[2] > 3:
			if player[1] == 39:
				test_team_1.append(player)
			elif player[1] == 40:
				test_team_2.append(player)	

#print(str(test_team_1))
#print(str(test_team_2))
team_1 = [player[3:] for player in test_team_1]
team_2 = [player[3:] for player in test_team_2]

avgs_team_1 = list(map(numpy.mean, zip(*team_1)))
avgs_team_2 = list(map(numpy.mean, zip(*team_2)))

print(str(avgs_team_1))
print(str(avgs_team_2))
test_predict = classifier.predict_proba([avgs_team_1, avgs_team_2])

percents = []
prob_team_1 = test_predict[0][1]
prob_team_2 = test_predict[1][1]
prob = prob_team_1 + prob_team_2
percents = [prob_team_1/prob, prob_team_2/prob]

print(str(percents))
