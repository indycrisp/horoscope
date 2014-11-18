import sqlite3
import numpy
from sklearn.naive_bayes import GaussianNB

conn = sqlite3.connect('horoscope.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

class Player():
	players = []

	def __init__(self, data):
		self.id = data['id']

	@classmethod
	def load(cls):
		c.execute('SELECT * FROM player')
		cls.players = [Player(data) for data in c.fetchall()]

	@classmethod
	def find(cls, id):
		for p in cls.players:
			if p.id == id:
				return p

	@property
	def player_matches(self):
		if not hasattr(self, '_player_matches'):
			self._player_matches = [pm for pm in PlayerMatch.playermatches if pm.player.id == self.id]
	
		return self._player_matches
	
	# player's average stats to date
	@property
	def avg_stats(self):
		if not hasattr(self, '_avg_stats'):
			stats = [pm.nb_stats for pm in self.player_matches]
			self._avg_stats = [sum(stat)/len(stat) for stat in zip(*stats)]

		return self._avg_stats

	@property
	def rpi(self):
		if not hasattr(self, '_rpi'):
			self._rpi = self.player_matches[-1].rpi

		return self._rpi

class PlayerMatch():
	playermatches = []
	
	def __init__(self, data):
		self.player = Player.find(data['player_id'])
		self.match_id = data['match_id']
		self.team_id = data['team_id']
		self.hero_id = data['hero_id']
		self.start_time = data['start_time']
		self.kills = data['kills']
		self.deaths = data['deaths']
		self.assists = data['assists']
		self.gpm = data['gpm']
		self.xpm = data['xpm']
		self.faction = 'r' if self.team_id == data['radiant_team_id'] else 'd'
		self.win = 1 if self.faction == 'r' and data['radiant_win'] or self.faction == 'd' and not data['radiant_win'] else 0
	
	@classmethod
	def load(cls):
		c.execute('SELECT * FROM playermatch, match where match.id = playermatch.match_id')
		cls.playermatches = [PlayerMatch(data) for data in c.fetchall() if Player.find(data['player_id'])]

	@property
	def nb_stats(self):
		if not hasattr(self, '_nb_stats'):
			self._nb_stats = [self.kills, self.deaths, self.assists, self.gpm, self.xpm, self.rpi]			

		return self._nb_stats

	# all matches to date for this player
	@property
	def matches_to_date(self):
		if not hasattr(self, '_matches_to_date'):
			self._matches_to_date = [pm for pm in self.player.player_matches if pm.player.id == self.player.id and pm.start_time <= self.start_time]
	
		return self._matches_to_date;

	# allies (including self) in this match
	@property
	def team(self):
		if not hasattr(Self, '_team'):
			self._team = [pm for pm in PlayerMatch.playermatches if pm.match_id == self.match_id and pm.faction == self.faction]
		return self._team

	# opponents in this match
	@property
	def opponents(self):
		if not hasattr(self, '_opponents'):
			self._opponents = [pm for pm in PlayerMatch.playermatches if pm.match_id == self.match_id and pm.faction != self.faction]
		
		return self._opponents

	# player's winning percentage up to and including this match
	@property
	def win_percent(self):
		if not hasattr(self, '_win_percent'):
			self._win_percent = sum(pm.win == 1 for pm in self.matches_to_date)/len(self.matches_to_date)

		return self._win_percent

	# opponents' winning percentages up to and including this match
	@property
	def owp(self):
		if not hasattr(self, '_owp'):
			self._owp = sum(o.win_percent for o in self.opponents)/len(self.opponents)
				
		return self._owp

	# opponents' opponent's winning percentages up to and including this match
	@property
	def oowp(self):
		if not hasattr(self, '_oowp'):
			oos = [oo for o in self.opponents for oo in o.opponents]
			self._oowp = sum(oo.win_percent for oo in oos)/len(oos)

		return self._oowp

	# player's RPI up to and including this match
	@property
	def rpi(self):
		if not hasattr(self, '_rpi'):
			self._rpi = (self.win_percent * 0.25) + (self.owp * 0.5) + (self.oowp * 0.25)		

		return self._rpi

	# player's average stats up to and including this match
	@property
	def avg_stats(self):
		if not hasattr(self, '_avg_stats'):
			stats_to_date = [pm.nb_stats for pm in self.matches_to_date]
			self._avg_stats = [sum(stat)/len(stat) for stat in zip(*stats_to_date)]			

		return self._avg_stats

class Team():
	teams = []

	def __init__(self, data):
		self.id   = data['id']
		self.name = data['name']
		self.p1   = Player.find(data['player1_id'])
		self.p2   = Player.find(data['player2_id'])
		self.p3   = Player.find(data['player3_id'])
		self.p4   = Player.find(data['player4_id'])
		self.p5   = Player.find(data['player5_id'])

	# get the team's current roster (as of their most recent game)
	@property
	def roster(self):
		if not hasattr(self, '_roster'):
			self._roster = [self.p1, self.p2, self.p3, self.p4, self.p5]
				
		return self._roster

	@classmethod
	def load(cls):
		c.execute('SELECT * FROM team')
		cls.teams = [Team(data) for data in c.fetchall()]
	
class NB():
	def __init__(self):
		self.nb = GaussianNB()

	@property
	def feature_vectors(self):
		if not hasattr(self, '_feature_vectors'):
			vectors = []
			for pm in PlayerMatch.playermatches:
				vectors.append(pm.avg_stats)

			self._feature_vectors = vectors
	
		return self._feature_vectors

	@property
	def results(self):
		if not hasattr(self, '_results'):
			self._results = [pm.win for pm in PlayerMatch.playermatches]
		
		return self._results

	def fit(self):
		self.nb.fit(self.feature_vectors, self.results)

	def score(self):
		print(str(self.nb.score(self.feature_vectors, self.results)))

	# get probabilities of every possible match-up
	def predict_all(self):
		for t1 in Team.teams:
			for t2 in Team.teams:
				if t1.id == 39 and t1.id != t2.id:
					p = self.predict(t1, t2)
					print(t1.name + ' | ' + str(p[0]) + ' - ' + str(p[1]) + ' | ' + t2.name)

	def predict(self, t1, t2):
		t1_stats = [[stat for stat in p.avg_stats] for p in t1.roster]
		t2_stats = [[stat for stat in p.avg_stats] for p in t2.roster]

		#print(str(t1_stats))
		#print(str(t2_stats))
		t1_avgs = [sum(stat)/len(stat) for stat in zip(*t1_stats)]
		t2_avgs = [sum(stat)/len(stat) for stat in zip(*t2_stats)]

		p = self.nb.predict_proba([t1_avgs, t2_avgs])
		
		t1_prob = p[0][1]
		t2_prob = p[1][1]
	
		return [round(100 * t1_prob/(t1_prob + t2_prob), 2), round(100 * t2_prob/(t1_prob + t2_prob), 2)]

if __name__ == '__main__':
	Player.load()
	PlayerMatch.load()
	Team.load()

	clsf = NB()
	clsf.fit()
	clsf.score()
	clsf.predict_all()
