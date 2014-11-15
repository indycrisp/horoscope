from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
	print "test"

if __name__ == "__main__":
	handler = RotatingFileHandler('steam_response.log', maxBytes=10000, backupCount = 1)
	handler.setLevel(logging.INFO)
	app.logger.addHandler(handler)
	app.run()
