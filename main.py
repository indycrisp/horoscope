from flask import Flask
import requests
import logging
import json
from logging.handlers import RotatingFileHandler

STEAM_KEY = '5D95A220441B79EDA8540E98E670082E'
STEAM_BASE_URL = 'https://api.steampowered.com/IDOTA2Match_570/'
MIN_LEAGUE_ID = 1886
MAX_LEAGUE_ID = 1888

app = Flask(__name__)

@app.route('/')
def getMatches():
	# get league ids
	leagues_response = requests.get(STEAM_BASE_URL + 'GetLeagueListing/V001/?key=' + STEAM_KEY)
	league_ids = []
	for league in leagues_response.json()['result']['leagues']:
		id = league['leagueid']
		if id > MIN_LEAGUE_ID:
			league_ids.append(id)

	# get match ids from each league
	match_ids = []
	for league_id in league_ids:
		matches_response = requests.get(STEAM_BASE_URL + 'GetMatchHistory/V001/' + '?league_id=' + str(league_id) + '&key=' + STEAM_KEY)

		matches = matches_response.json()['result']['matches']
		for match in matches:
			match_ids.append(match['match_id'])


	# get match details for each match id
	full_matches = []
	for match_id in match_ids:
		match_response = requests.get(STEAM_BASE_URL + 'GetMatchDetails/V001/' + '?match_id=' + str(match_id) + '&key=' + STEAM_KEY)

		
	app.logger.info('Info')
	return str(match_ids)

if __name__ == "__main__":
	handler = RotatingFileHandler('steam_response.log', maxBytes=10000, backupCount = 1)
	handler.setLevel(logging.INFO)
	app.logger.addHandler(handler)
	app.run()
