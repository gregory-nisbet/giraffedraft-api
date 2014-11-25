import bottle
from bottle import route, run, template, post, get, response, request
from json import dumps, loads

import random

from copy import copy

import socket

import re

import test

from parser import data, means
#from parser import data

from logic import VectorCollection

# enable app

app = bottle.app()


def do_snd(fun):
	return lambda x : fun(x[1])


# NOTE: no average draft pick in numeric keys!
numeric_keys = r"3PTM AST BLK FG% FGA FGM FT% FTA FTM PTS REB ST TO".split(" ")

team_keys = "team draftPosition isPlayer".split(" ")

team_name_regex = re.compile(r"\w{,3} \-")

string_assoc = lambda d : [ (str(k), str(v)) for k,v in d.items() ]

name_to_id = {}

def game_state_to_array(obj):
	assert isinstance(obj, dict)

	# prehistory is not in chronological order
	# because it actually doesn't matter (and we can't recover that information)
	prehistory = []

	player_index = None

	players = len(obj)

	for key, value in obj.iteritems():
		assert set(value.keys()) == set(team_keys)

		vectors = value["team"]

		if (value["isPlayer"]):
			player_index = value["draftPosition"]-1

		for yahoo_rank, vector_obj in vectors.iteritems():
			my_vector = {}
			for k,v in vector_obj.iteritems():
				if k in numeric_keys:
					my_vector[k] = float(v)
				else:
					my_vector[k] = v

			my_vector["yahoo-rank"] = yahoo_rank

			vector_name = team_name_regex.split(vector_obj["playerName"])[0].strip()

			my_vector["name"] = vector_name

			# global name to id map

			prehistory.append( (value["draftPosition"]-1, my_vector) )

	#print "prehistory"
	#print map(do_snd(string_assoc), prehistory)

	return {"prehistory" : map(do_snd(string_assoc), prehistory), "player_index" : player_index, "players" : players}





# sample data

sample = ("""{
    "player1": {"2":{"injured":false,"ADP":"2.6","FGM":"583","FGA":"1102","FG%":".530","FTM":"326","FTA":"411","FT%":".793","3PTM":"2.5","PTS":"1496","REB":"682","AST":"112","ST":"107","BLK":"202","TO":"110","playerName":"Anthony Davis NO - PF,C"}},
    "player2: {
"12":{"injured":false,"ADP":"14.5","FGM":"608","FGA":"1222","FG%":".498","FTM":"172","FTA":"236","FT%":".728","3PTM":"1.6","PTS":"1389","REB":"675","AST":"136","ST":"59.5","BLK":"87.0","TO":"94.9","playerName":"Al Jefferson Cha - PF,C"},
"17":{"injured":false,"ADP":"20.9","FGM":"462","FGA":"967","FG%":".478","FTM":"345","FTA":"422","FT%":".819","3PTM":"65.7","PTS":"1336","REB":"556","AST":"137","ST":"65.7","BLK":"61.2","TO":"122","playerName":"Chris Bosh Mia - PF,C"}}
  }""")


players = VectorCollection.create(dicts = data, means = means, numeric_keys = numeric_keys)

players_list = []

for row in players.list:
	name_to_id[row.data["name"]] = row.id

	players_list.append( [("name", row.data["name"]), ("id", row.id)] + [ (str(k), str(v)) for k,v in row.items() ] )

thing = players.list[0]

# print [key for key in thing]

# print "=" * 10
# print "created!"
# print "=" * 10

# foo = players.query(
# 	top_n = 5,
# 	n = 12,
# 	player_index = 0,
# 	players = 3,
# 	history = None,
# 	horizon = 3,
# 	prehistory = None,
# 	sweep = 1
# )

# print "\n".join([str(foo[x][0][1]) for x in range(5)])

def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors

@app.route('/api', method = "GET")
@enable_cors
def index():
	return "welcome to the API! Enjoy your stay"

@app.route('/api/allPlayers', method = "GET")
@enable_cors
def index():
	response.content_type = "application/json"
	return dumps(data)

@app.route('/api/means', method = "GET")
@enable_cors
def index():
	response.content_type = "application/json"
	return dumps(means)


@app.route('/test/suggest', method = ["OPTIONS", "POST"] )
@enable_cors
def index():
	response.content_type = "application/json"
	keys = r"3PTM ADP AST BLK FG% FGA FGM FT% FTA FTM PTS REB ST TO".split(" ")

	out = []
	for x in range(3):
		fake_player = { k : random.random() for k in keys }
		fake_player["injured"] = True
		fake_player["playerName"] = "Player #" + str(random.random())
		out.append(fake_player)

	return dumps(out)

@app.route('/api/suggest', method = ["OPTIONS", "POST"])
@enable_cors
def index():
	all_items = request.forms.allitems()
	request_data = loads(all_items[0][0])

	game_obj = game_state_to_array(request_data)

	complete_cycle_count = int( len(game_obj["prehistory"])/game_obj["players"] )

	picked_already = []

	# for player_idx,obj in game_obj["prehistory"]:
	# 	picked_already.append( name_to_id[obj["name"]] )

	if complete_cycle_count % 2 == 0:
		sweep_direction = 1
	else:
		sweep_direction = -1

	# n is wrong!
	# doesn't remove players who have already been drafted
	haskell_args = dumps( dict(
		n = 10,
		playerIndex = 0,
		history = [], #game_obj["player_index"],
		preHistory = [], # game_obj["prehistory"],
		inventory = [[["a","5"]], [["a","7"]]], # players_list,
		sweep = 1, # sweep_direction,
		players = 2, # game_obj["players"],
		horizon = 1,
		ignoreFirst = [] # [picked_already],
	) )

	sample = "{\"players\" : 4, \"n\" : 2, \"playerIndex\" : 2,\"history\" : [],\"horizon\" : 1,\"preHistory\" : [],\"sweep\" : 1,\"ignoreFirst\" : [],\"inventory\" : [[[\"a\",\"4\"]], [[\"a\", \"5\"]]]}"

	print sample
	# with open("frodo.txt", "w") as f:
	# 	f.write(haskell_args)

	a = test.query(sample)




	return a


hostname = socket.gethostname()

if hostname == "shotcallerapi":
	run(host='0.0.0.0', port=8080)
else:
	run(host='localhost', port=8080)
