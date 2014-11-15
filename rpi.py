import sqlite3

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
            for m in player.matches:
                opposing_team = m.r_team if player in m.d_team.players else m.d_team
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
                self._OWP = 0

            else:
                oowp = 0
                for o in self.opponents:
                    oowp += o.OWP
                self._OOWP = oowp/len(self.opponents)
        return self._OOWP

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


# https://en.wikipedia.org/wiki/Rating_Percentage_Index
def rating_percentage_index(player):
    return (player.WP * 0.25) + (player.OWP * 0.5) + (player.OOWP * 0.25)


if __name__ == '__main__':
    Team.load()
    Player.load()
    Match.load()

    # Calculate and save win percentages.
    for player in Player.players:
        print(rating_percentage_index(player))
