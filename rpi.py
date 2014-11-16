import sqlite3
import numpy
from sklearn.naive_bayes import GaussianNB

conn = sqlite3.connect('horoscope.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()


class Team():
    teams = []

    def __init__(self, data):
        self.id      = int(data['id'])
        self.name    = data['name']
        self.players = []

    @classmethod
    def load(cls):
        c.execute('SELECT * FROM team')
        cls.teams = [Team(data) for data in c.fetchall()]

    @classmethod
    def find(cls, id):
        return next((t for t in cls.teams if t.id == id), None)



class Player():
    players = []

    def __init__(self, id, team_id):
        self.id = id
        self.team = Team.find(team_id)
        self.team.players.append(self)
        self.matches = []

    def winning_percentage(self, matches=None):
        if matches is None:
            matches = self.matches

        matches_played = len(matches)
        matches_won    = 0

        if matches_played == 0:
            return 0

        for m in matches:
            winning_team = m.r_team if m.r_win else m.d_team
            if self in winning_team.players:
                matches_won += 1
        return matches_won/float(matches_played)

    @property
    def WP(self):
        if not hasattr(self, '_WP'):
            self._WP = self.winning_percentage()
        return self._WP

    @property
    def opponents(self):
        if not hasattr(self, '_opponents'):
            opponents = []
            for m in self.matches:
                opposing_team = m.r_team if self in m.d_team.players else m.d_team
                opponents += [o for o in opposing_team.players]
            self._opponents = set(opponents)
        return self._opponents

    @property
    def OWP(self):
        if not hasattr(self, '_OWP'):
            if len(self.opponents) == 0:
                self._OWP = 0

            else:
                owp = 0
                for o in self.opponents:
                    owp += o.winning_percentage([m for m in o.matches if self not in m.players])
                self._OWP = owp/len(self.opponents)
        return self._OWP

    @property
    def OOWP(self):
        if not hasattr(self, '_OOWP'):
            if len(self.opponents) == 0:
                self._OOWP = 0

            else:
                oowp = 0
                for o in self.opponents:
                    oowp += o.OWP
                self._OOWP = oowp/len(self.opponents)
        return self._OOWP

    # https://en.wikipedia.org/wiki/Rating_Percentage_Index
    @property
    def rpi(self):
        if not hasattr(self, '_rpi'):
            self._rpi = (self.WP * 0.25) + (self.OWP * 0.5) + (self.OOWP * 0.25)
        return self._rpi

    @property
    def avg_stats(self):
        if not hasattr(self, '_avg_stats'):
            player_stats = [playermatch.game_stats for playermatch in self.player_matches]
            self._avg_stats = [sum(stat)/len(stat) for stat in zip(*player_stats)]
        return self._avg_stats

    @property
    def player_matches(self):
        if not hasattr(self, '_player_matches'):
            self._player_matches = [playermatch for playermatch in PlayerMatch.playermatches if playermatch.player.id == self.id]
        return self._player_matches

    @classmethod
    def load(cls):
        c.execute('SELECT * FROM player');
        cls.players = [Player(id, team_id) for id, team_id in c.fetchall()]

    @classmethod
    def find(cls, id):
        return next((p for p in cls.players if p.id == id), None)

class Match():
    matches = []

    def __init__(self, data):
        self.id      = int(data['id'])
        self.r_win   = True if data['radiant_win'] == 'Y' else False
        self.r_team  = Team.find(int(data['radiant_team_id']))
        self.d_team  = Team.find(int(data['dire_team_id']))
        self.players = []

    @classmethod
    def load(cls):
        c.execute('SELECT * FROM match')
        cls.matches = [Match(data) for data in c.fetchall()]

        c.execute('SELECT * FROM playermatch')
        for pm in c.fetchall():
            match = cls.find(pm['match_id'])
            player = Player.find(pm['player_id'])
            match.players.append(player)
            player.matches.append(match)

    @classmethod
    def find(cls, id):
        return next((m for m in cls.matches if m.id == id), None)

class PlayerMatch():
    playermatches = []

    def __init__(self, data):
        self.player        = Player.find(int(data['player_id']))
        self.match         = Match.find(int(data['match_id']))
        self.team          = self.player.team
        self.hero_id       = int(data['hero_id'])
        self.kills         = int(data['kills'])
        self.deaths        = int(data['deaths'])
        self.assists       = int(data['assists'])
        self.gold          = int(data['gold'])
        self.last_hits     = int(data['last_hits'])
        self.denies        = int(data['denies'])
        self.gpm           = int(data['gpm'])
        self.xpm           = int(data['xpm'])
        self.gold_spent    = int(data['gold_spent'])
        self.hero_damage   = int(data['hero_damage'])
        self.tower_damage  = int(data['tower_damage'])
        self.hero_healing  = int(data['hero_healing'])
        self.game_stats    = [self.kills, self.deaths, self.assists, self.last_hits, self.denies, self.gpm, self.xpm, self.hero_damage, self.hero_healing]

        #TODO: WHY ARE THERE MORE LOSSES THAN WINS TOTAL
        if (
            self.team.id == self.match.r_team.id and self.match.r_win
            or self.team.id == self.match.d_team.id and not self.match.r_win
        ):
            self.win = 1

        else:
            #print(str(self.team.id) + " " + str(self.match.r_team.id) + " " + str(self.match.r_win))
            self.win = 0

    @classmethod
    def load(cls):
        c.execute('SELECT * FROM playermatch')
        cls.playermatches = [PlayerMatch(data) for data in c.fetchall()]            

def fit_classifier(training_vectors, targets):
    classifier = GaussianNB()
    classifier.fit(training_vectors, targets)
    return classifier

def get_percentages(probabilities):
    prob_team_1 = probabilities[0][1]
    prob_team_2 = probabilities[1][1]
    percent_team_1 = prob_team_1 / (prob_team_1 + prob_team_2)
    percent_team_2 = prob_team_2 / (prob_team_1 + prob_team_2)
    return [percent_team_1, percent_team_2]

if __name__ == '__main__':
    Team.load()
    Player.load()
    Match.load()
    PlayerMatch.load()

    vectors = []
    results = []
    for playermatch in PlayerMatch.playermatches:
        #vectors.append([playermatch.player.rpi])
        vectors.append([stat * playermatch.player.rpi for stat in playermatch.game_stats])
        results.append(playermatch.win)

    classifier = fit_classifier(vectors, results)
    print(str(classifier.score(vectors, results)))

    #TODO: figure out what to give the classifier for upcoming matches.  right now it's an avg stats of the players on each team
    test_team_1 = Team.find(39) #EG
    test_team_2 = Team.find(40) #VP
    
    test_team_1_stats = [[stat * player.rpi for stat in player.avg_stats] for player in test_team_1.players[:5]]
    test_team_2_stats = [[stat * player.rpi for stat in player.avg_stats] for player in test_team_2.players[:5]]
    
    test_team_1_avg = [sum(stat)/len(stat) for stat in zip(*test_team_1_stats)]
    test_team_2_avg = [sum(stat)/len(stat) for stat in zip(*test_team_2_stats)]
    
    test_predict = classifier.predict_proba([test_team_1_avg, test_team_2_avg])
    odds = get_percentages(test_predict)
    
    print(str(odds))
