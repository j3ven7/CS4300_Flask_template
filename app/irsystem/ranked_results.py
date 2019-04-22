import csv
import os, sys
import googlemaps
from nltk.tokenize import TreebankWordTokenizer
from datetime import datetime
import numpy as np
from math import sin, cos, sqrt, atan2, radians, log10
import scipy.spatial.distance as s

def queryToVec(query, model):
    """
    Takes a string query and converts it to a word embedding by taking the average of the words in the query
    
    Args:
        query    - array representation of string that we are using for search
        model    - dictionary mapping words to embeddings
    
    Returns:
        Array (embedding) representation of the query
    """
    length = 0
    
    # Just a place holder so we know the length of the embeddings
    rst = 0
    
    for word in query:
        try:
            rst += model[word.lower()]
            length += 1
        except:
            pass
    
    return (0 if length == 0 else rst / length) 


def computeTopTypes(query, all_types, model):
    """
    Takes a query and a string of types and determines its score
    
    Args:
        query        - array representation of string that we are using for search
        all_types    - set of all types contained by our places
        model        - dictionary mapping words to embeddings
        
    Returns:
        Ranked types by our query
    """
    query_vec = queryToVec(query, model)
    rst = {}
    # Iterating through our types
    for t in all_types:
        try:
            score = s.cosine(query_vec, model[t.lower()])
            rst[t] = score
        # But types could be "point_of_interest"
        except:
            try:
                tmp = t.split("_")
                tmp_vec = queryToVec(tmp, model)
                score = s.cosine(query_vec, tmp_vec)
                rst[t] = score
            except:
                print(t, " was not in the dictionary")
        
    return sorted(rst.items(), key=lambda item : item[1], reverse=False)
    
def computeScore(query, types, model):
    """
    Takes a query and a string of types and determines its score
    
    Args:
        query    - array representation of string that we are using for search
        types    - string like 'museums, point_of_interest, florist' 
        model    - dictionary mapping words to embeddings
    
    Returns:
        Tuple of the score for the place and the associated type
    """
    final_score = 0
    
    # First we convert our query to a vector
    query_vec = queryToVec(query, model)
    
    # Now we need to convert our types
    types = types.split(",")
    length = len(types)
    
    # Iterating through our types
    for t in types:
        try:
            score = s.cosine(query_vec, model[t.lower()])
            final_score += score
        # But types could be "point_of_interest"
        except:
            try:
                tmp = t.split("_")
                tmp_vec = queryToVec(tmp, model)
                score = s.cosine(query_vec, tmp_vec)
                final_score += score
            except:
                print(t, len(t), " was not in the dictionary")
                
    return (final_score / length)

def getTopPlacesTypes(places_to_details, query, model):
    """
    Gets top places based on embeddings related to type
    
    Args:
        places_to_details    - dictionary of places to their details
        query                - array representation of string that we are using for search
        model                - dictionary mapping words to embeddings
    
    Returns
        The top places for our search
    """
    rst = {}
    
    for place in places_to_details:        
        types = places_to_details[place]['types']
        score = computeScore(query, types, model)
        rst[place] = score

    
    return sorted(rst.items(), key=lambda item : item[1], reverse=False)
def computeDistanceLatLong(lat1, lon1, lat2, lon2):
	"""
	Computes distance in km between two locations using lat long 

	"""
	# approximate radius of earth in km
	R = 6373.0

	lat1 = radians(lat1)
	lon1 = radians(lon1)
	lat2 = radians(lat2)
	lon2 = radians(lon2)

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	distance = R * c

	return distance
def getDistanceToRoute(waypoints, lat, lng):
    """
    Returns the distnace to the route (METERS) for a given location (takes minimum of waypoints)
    NOTE: This doesn't make any live API calls, it just takes vectors as a relative measurement
    
    Args:
        waypoints - list of waypoints on the path
        lat       - latitude for a given place
        lng       - longitude for a given place 
    """
    min_distance = sys.maxsize
    
    for waypoint in waypoints:
        lat_waypoint = waypoint[0]
        lng_waypoint = waypoint[1]
        distance = computeDistanceLatLong(lat_waypoint, lng_waypoint, lat, lng)
        
        if distance < min_distance:
            min_distance = distance

    return min_distance*1000

# 1. Need to generate a route and waypoints based on start and end location
# - User should also provide keywords 
# 2. Based on keywords they care about look at reviews and try to find the most closely related document
def generateWaypoints(start_addr, end_addr):
    """
    Generates a route between a start and end address

    Returns an array of waypoints along the route
    """
    rst = []

    gmap = googlemaps.Client(key=os.environ["GOOGLE_KEY"])

    # Request directions via public transit
    now = datetime.now()

    # The locations can be written out or geocoded
    # mode = "driving", "walking", "bicycling", "transit"
    # departure_time -- int or date.datetime
    directions_result = gmap.directions(start_addr,
                                         end_addr,
                                         mode="driving",
                                         departure_time=now)

    # Way to lookup waypoints for later usage
    waypoint_dict = directions_result[0]["legs"][0]["steps"]
    # Use this to determine splits
    trip_distance = directions_result[0]['legs'][0]['distance']['value']
    
    
    total_distance = 0 # total distance in meters
    total_duration = 0 # total duration in seconds

    prev_distance = 0

    waypoints = [] # tuples of (lat, lng)
    polylines = [] # Array of polylines -- can be used for display if we like

    for entry in waypoint_dict:
        total_distance += entry["distance"]["value"]
        total_duration += entry["duration"]["value"]

        # Now we want to include as many waypoints as possible
        # Since computing distance to waypoints is super cheap
        if True: 
            lat = entry["start_location"]["lat"]
            lng = entry["start_location"]["lng"]
            waypoints.append((lat, lng))
            prev_distance = total_distance
            
        polylines.append(entry["polyline"]["points"])

    return waypoints

def index_search(query, index, idf, doc_norms, tokenizer=TreebankWordTokenizer()):
    """ Search the collection of documents for the given query
    
    Arguments
    =========
    
    query: string,
        The query we are looking for.
    
    index: an inverted index as above
    
    idf: idf values precomputed as above
    
    doc_norms: document norms as computed above
    
    tokenizer: a TreebankWordTokenizer
    
    Returns
    =======
    
    results, list of tuples (score, doc_id)
        Sorted list of results such that the first element has
        the highest score, and `doc_id` points to the document
        with the highest score.
    
    Note: 
        
    """
    # How do I get the norm q? I think I just need the term count for the query and compute the norm using the idf
    query = tokenizer.tokenize(query.lower())
   
    #### START GETTING Q norm ####
    q_counts = {}
    q_norm = 0

    # This gives us the term frequency in the query
    for term in query:
        if term in idf:
            if term not in q_counts:
                q_counts[term] = 0
            q_counts[term] += 1

    # This is the sum of the (tf_i * idf_i)**2
    for k in q_counts:
        q_norm += (q_counts[k] * idf[k])**2
        
    
    q_norm = np.sqrt(q_norm)
    
    #### END GETTING Q norm ####
    
    scores = {}
    rst = []
    
    # First iterate over every term
    for term in query:
        if term in idf:
            # Check what docs the query is in 
            term_tups = index[term]
            # q_i: See how many times the term appears in the query
            term_count = q_counts[term]
            for tup in term_tups:
                # This is computing q_i * d_ij
                if tup[0] not in scores:
                    scores[tup[0]] = 0
                scores[tup[0]] += (q_counts[term] * idf[term]) * (tup[1] * idf[term])
    
    # Includes logic in here to divide by norms and such        
    rst = {i : (scores[i] / (q_norm * doc_norms[i])) for i in scores.keys()}
    

    
    return rst

def computeScores(waypoints, query, model, index_search_rst_reviews, index_search_rst_types, 
                  review_to_places, places_to_details, max_dist):
    """
    Takes scores that we get from our index search against types and reviews and computes
    distances between each place to rank our results
    
    Args:
        waypoints                 - a list of waypoints along the route
        query                     - array representation of string that we are using for search
        model                     - dictionary mapping words to embeddings
        index_search_rst_reviews  - dictionary of review id to tf-idf score of that review against our query
        index_search_rst_types    - dictionary of review id to tf-idf score of types for the place against our query
        review_to_places          - dictionary of review id to name of the corresponding place
        places_to_details         - dictionary of place name to details about that place (i.e. lat/lng, reviews, rating, etc.)
        max_dist                  - int max distance willing to deviate from the
    Return:
        Dictionary mapping a place to its score 
    """
    seen_review_ids    = set() # Set of each seen id so far
    overlap_ids = set() 

    places = places_to_details.keys()
    
    # Remember to take EACH review into account
    place_data = {} # Dictionary mapping place names to a "score" and "count" (for normalization) and "distance" 
    
    # NOTE: Here I am just trying to speed things up by looking for overlap 
    # between types and reviews and our query - if the user
    # searches for museum it will show up in types and reviews
    for k in index_search_rst_reviews:
        if k in index_search_rst_types:
            overlap_ids.add(k)
    
    #print(overlap_ids)
    
    # We have sufficient reviews with overlapping types
    if len(overlap_ids) > 20:
        for key in overlap_ids:
            curr_place         = review_to_places[key]
            # Here I am just using some arbitrary multiplier to count the reviews more heavily*
            curr_score         = ((index_search_rst_reviews[key]*2) + index_search_rst_types[key]) / 2
        
            # Each place can have multiple reviews:

            # 1. We have not come across a review from the same place 
            if curr_place not in place_data:
                place_data[curr_place] = {"score" : curr_score, "count" : 1, "distance": None}
            # 2. We have already come across a review from the same place
            else:
                # Need to figure out what our score was in order to change it
                score = place_data[curr_place]["score"]
                count = place_data[curr_place]["count"]
                place_data[curr_place]["score"] = score + curr_score
                place_data[curr_place]["count"] = count + 1

            # Computing distance information
            if place_data[curr_place]["distance"] == None:
                curr_place_details = places_to_details[curr_place]
                curr_lat           = float(curr_place_details['lat'])
                curr_lng           = float(curr_place_details['lng'])
                curr_distance      = getDistanceToRoute(waypoints, curr_lat, curr_lng)

                # This stores the distances - higher score if you are closer
                place_data[curr_place]["distance"] =  curr_distance           
    
    # No entries in the query that were included in our types
    else:
        # Takes all unique results - some are words that appeared in a review, others are types, some are both
        all_keys = list(set(list(index_search_rst_reviews.keys()) + list(index_search_rst_types.keys())))
        print("all_keys: ", all_keys)
        # NOTE: We can include a distance threshold here and throw places out based on distance
        for key in all_keys:
            curr_place         = review_to_places[key]
            curr_score         = index_search_rst_reviews[key]

            if curr_place not in place_data:
                place_data[curr_place] = {"score" : curr_score, "count" : 1, "distance": None}
            else:
                score = place_data[curr_place]["score"]
                count = place_data[curr_place]["count"]
                place_data[curr_place]["score"] = score + curr_score
                place_data[curr_place]["count"] = count + 1

            # Ensure we don't double count when checking types
            seen_review_ids.add(key)

            if place_data[curr_place]["distance"] == None:
                curr_place_details = places_to_details[curr_place]
                curr_lat           = float(curr_place_details['lat'])
                curr_lng           = float(curr_place_details['lng'])
                curr_distance      = getDistanceToRoute(waypoints, curr_lat, curr_lng)

                # This stores the distances - higher score if you are closer
                place_data[curr_place]["distance"] =  curr_distance
                
    
    final_rst = {} # Mapping of place to final score -- including distance
    print("places length: ", len(places))
    for k in places: # Keys are the places 
        #eliminate results more than max distance allowed from route
        # if place_data[k]["distance"]/1609.344 > max_dist:
        #     continue
        
        # Compute score wrt embeddings
        types = places_to_details[k]["types"]
        types_score  = computeScore(query, types, model)
        print("types_score: ", types_score)

        # TODO: Include distance in our score -- place_distances[k] -- in some way
        final_rst[k] = {}
        if k in place_data:
            score = place_data[k]["score"]
            count = place_data[k]["count"]
        else:
            score = 0
            count = 1
        
        final_rst[k]['lat'] = places_to_details[k]['lat']
        final_rst[k]['long'] = places_to_details[k]['lng']
        final_rst[k]['address'] = places_to_details[k]['address']
        final_rst[k]['rating'] = places_to_details[k]['ratings']
        final_rst[k]['review'] = places_to_details[k]['pos_review']

        #low score results that are not "on the way" or  too close to origin/destination
        origin = np.array(waypoints[0])
        destination = np.array(waypoints[-1])
        lat_lng = np.array((float(places_to_details[k]['lat']),float(places_to_details[k]['lng'])))
        signs = np.sign(origin-destination) + np.sign(origin-lat_lng)
        if (np.count_nonzero(signs) == 0 or computeDistanceLatLong(lat_lng[0],lat_lng[1],waypoints[0][0],waypoints[0][1]) < 16.0934
or computeDistanceLatLong(lat_lng[0],lat_lng[1],waypoints[-1][0],waypoints[-1][1]) < 16.0934):
            final_rst[k]['score'] = -1
        else:
            try:
                rating_score = log10(float(final_rst[k]['rating']))/3
            except:
                rating_score = 0
            final_rst[k]['score'] = (rating_score + (score / count) + (.1/(types_score + .001)))

    return sorted(final_rst.items(), key=lambda kv: kv[1]['score'], reverse=True)

    
