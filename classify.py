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
			stats = [pm.classification_stats for pm in self.player_matches]
			self._avg_stats = [sum(stat)/len(stat) for stat in zip(*stats)]
			print(str(self._avg_stats))

		return self._avg_stats

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
		self.classification_stats = [self.kills, self.deaths, self.assists, self.gpm, self.xpm]
		self.faction = 'r' if self.team_id == data['radiant_team_id'] else 'd'
		self.win = 1 if self.faction == 'r' and data['radiant_win'] or self.faction == 'd' and not data['radiant_win'] else 0
	
	@classmethod
	def load(cls):
		c.execute('SELECT * FROM playermatch, match where match.id = playermatch.match_id')
		cls.playermatches = [PlayerMatch(data) for data in c.fetchall()]

	# all matches to date for this player
	@property
	def matches_to_date(self):
		if not hasattr(self, '_matches_to_date'):
			self._matches_to_date = [pm for pm in self.player.player_matches if pm.player.id == self.player.id and pm.start_time <= self.start_time]
	
		return self._matches_to_date;

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
			stats_to_date = [pm.classification_stats for pm in self.matches_to_date]
			self._avg_stats = [sum(stat)/len(stat) for stat in zip(*stats_to_date)]			

		return self._avg_stats

class NB():
	def __init__(self):
		self.nb = GaussianNB()

	@property
	def feature_vectors(self):
		if not hasattr(self, '_feature_vectors'):
			vectors = []
			for pm in PlayerMatch.playermatches:
				vectors.append([pm.rpi * stat for stat in pm.avg_stats])

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
		return self.nb.score(self.feature_vectors, self.results)	

if __name__ == '__main__':
	Player.load()
	PlayerMatch.load()

	clsf = NB()
	clsf.fit()
	print(str(clsf.score()))
