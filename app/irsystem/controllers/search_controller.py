from . import *  
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
import os, sys
from app.irsystem import ranked_results as rr

from googleplaces import types
import googlemaps

import pickle
from nltk import PorterStemmer


net_id = "Josh Even (jre83), Josh Sones (js2572), Adomas Hassan (ah667), Jesse Salazar (js2928), Luis Verdi (lev27)"
API_KEY = os.environ["GOOGLE_KEY"]
client = googlemaps.Client(API_KEY)

# Josh TODO: Move this into its own file
def loadGloveModel(gloveFile):
    """
    Loads in gloveFile which contains word vectors
    Returns -- dictionary with word keys and tuple values
        Ex: model["Word"] = ([x1,x1,...,xn], magnitude)
        Where the magnitude is the norm of the vector
    """
    
    print("Loading Glove Model")
    f = open(gloveFile,'r')
    model = {}
    for line in f:
        splitLine = line.split()
        word = splitLine[0]
        embedding = np.array([float(val) for val in splitLine[1:]]) if len(splitLine) <= 100 else np.array([float(splitLine[i]) for i in range(1, 200)])
        #magnitude = np.linalg.norm(embedding)
        model[word] = embedding #, magnitude)
    return model

print("Loading SVD Model")
with open("./app/irsystem/pickled_svd","rb") as f:
    close_words = pickle.load(f)
            
big_model   = loadGloveModel('GloVe-1.2/vectors.txt')
# print(len(big_model))

@irsystem.route('/', methods=['GET'])
def search():
	origin = request.args.get('origin')
	destination = request.args.get('dest')
	try:
		queries = [r.lower() for r in request.args.get('description').split(',')]
	except:
		queries = [""]
	try:
		max_dist = int(request.args.get('distance'))
	except:
		max_dist = 3000

	if not (origin and destination):
		data = []
		output_message = ''
		results = []
		inputs = []
	else:
		inputs = [origin, destination]
		output_message = "Your search: " + origin + " to " + destination
        # this is where the results get populated in
		print("getting results")
		with open("./app/irsystem/pickled_data_v2","rb") as f:
			inv_idx_reviews,idf_reviews,doc_norms_reviews,inv_idx_types,idf_types,doc_norms_types, review_to_places, places_to_details = pickle.load(f)
		try :
			waypoints = rr.generateWaypoints(origin, destination)
		except:
			return render_template('search.html', netid=net_id, output_message=output_message, inputs=inputs, queries=request.args.get('description'), dist=request.args.get('distance'), results=[], api_key=API_KEY)
		results = []
		punc = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
		stemmer = PorterStemmer()
		for query in queries:
			# This is used for searching against our word embeddings matrix
			query_embedding = ''.join(c for c in query if c not in punc)
			#print("Query: ", query_embedding)
			
			# This is used for searching against our tf-idf matrix
			# convert to an array and stem each individual word
			query = query.split(" ")
			query = [stemmer.stem(k) for k in query]
			# Make sure the words themselves are kosher
			for i in range(len(query)):
				query[i] = ''.join(c for c in query[i] if c not in punc)
			
			# Need to feed a string to our search results so rejoin the results
			query = ' '.join([q for q in query])
			#print("query: ", query)
			index_search_rst_reviews = rr.index_search(query, inv_idx_reviews, idf_reviews, doc_norms_reviews)
			index_search_rst_types = rr.index_search(query, inv_idx_types, idf_types, doc_norms_types)
			ranked_rst = rr.computeScores(waypoints, query_embedding, big_model, index_search_rst_reviews, index_search_rst_types, review_to_places, places_to_details, max_dist, close_words)
			results.append(ranked_rst[:10])
	return render_template('search.html', netid=net_id, output_message=output_message, inputs=inputs, queries=request.args.get('description'), dist=request.args.get('distance'), results=results, api_key=API_KEY)
