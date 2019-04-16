import csv
import os, sys
import googlemaps
from nltk.tokenize import TreebankWordTokenizer
from datetime import datetime
import numpy as np
from math import sin, cos, sqrt, atan2, radians

def computeDistanceLatLong(lat1, lon1, lat2, lon2):
	"""
	Computes distance between two locations using lat long 

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
    Returns the distnace to the route for a given location (takes minimum of waypoints)
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

    return min_distance

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
        if total_distance - prev_distance > 5000: 
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

def computeScores(waypoints, index_search_rst_reviews, index_search_rst_types, 
                  review_to_places, places_to_details, max_dist):
    """
    Takes scores that we get from our index search against types and reviews and computes
    distances between each place to rank our results
    
    Args:
        waypoints                 - a list of waypoints along the route
        index_search_rst_reviews  - dictionary of review id to tf-idf score of that review against our query
        index_search_rst_types    - dictionary of review id to tf-idf score of types for the place against our query
        review_to_places          - dictionary of review id to name of the corresponding place
        places_to_details         - dictionary of place name to details about that place (i.e. lat/lng, reviews, rating, etc.)
        
    Return:
        Dictionary mapping a place to its score 
    """
    place_distances    = {} # Dictionary mapping place names to the distance to the path
    seen_review_ids    = set() # Set of each seen id so far
    
    # Remember to take EACH review into account
    place_scores_and_counts = {} # Dictionary mapping place names to a tuple of scores and counts for normalization
    
    overlap_ids = set() 
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
            # Here I am just using some arbitrary multiplier to count the reviews more since
            # we know they all have a type included in the query
            curr_score         = ((index_search_rst_reviews[key]*2) + index_search_rst_types[key]) / 2
        
            # This code is for when we have no type overlap but we can omit this for now
            # This is the first review associated with the place
            if curr_place not in place_scores_and_counts:
                place_scores_and_counts[curr_place] = (curr_score, 1)
            else:
                score = place_scores_and_counts[curr_place][0]
                count = place_scores_and_counts[curr_place][1]
                place_scores_and_counts[curr_place] = (score + curr_score, count + 1)

            if curr_place not in place_distances:
                curr_place_details = places_to_details[curr_place]
                curr_lat           = float(curr_place_details['lat'])
                curr_lng           = float(curr_place_details['lng'])
                curr_distance      = getDistanceToRoute(waypoints, curr_lat, curr_lng)

                # This stores the distances - higher score if you are closer
                place_distances[curr_place] =  1 / curr_distance           
    
    # Not enough types in the query 
    else:
        # NOTE: We can include a distance threshold here and throw places out based on distance
        for key in index_search_rst_reviews:
            curr_place         = review_to_places[key]
            curr_score         = index_search_rst_reviews[key]

            # This is the first review associated with the place
            if curr_place not in place_scores_and_counts:
                place_scores_and_counts[curr_place] = (curr_score, 1)
            else:
                score = place_scores_and_counts[curr_place][0]
                count = place_scores_and_counts[curr_place][1]
                place_scores_and_counts[curr_place] = (score + curr_score, count + 1)

            # Ensure we don't double count when checking types
            seen_review_ids.add(key)

            if curr_place not in place_distances:
                curr_place_details = places_to_details[curr_place]
                curr_lat           = float(curr_place_details['lat'])
                curr_lng           = float(curr_place_details['lng'])
                curr_distance      = getDistanceToRoute(waypoints, curr_lat, curr_lng)

                # This stores the distances - higher score if you are closer
                place_distances[curr_place] =  1 / curr_distance
        
        for key in index_search_rst_reviews:
            curr_place         = review_to_places[key]
            curr_score         = index_search_rst_reviews[key] 

            # This is the first review associated with the place
            if curr_place not in place_scores_and_counts:
                place_scores_and_counts[curr_place] = (curr_score, 1)
            else:
                score = place_scores_and_counts[curr_place][0]
                count = place_scores_and_counts[curr_place][1]
                # This prevents double counting of reviews and types
                if key not in seen_review_ids:
                    place_scores_and_counts[curr_place] = (score + curr_score, count + 1)
                else:
                    place_scores_and_counts[curr_place] = (score + curr_score, count)


            if curr_place not in place_distances:
                curr_place_details = places_to_details[curr_place]
                curr_lat           = float(curr_place_details['lat'])
                curr_lng           = float(curr_place_details['lng'])
                curr_distance      = getDistanceToRoute(waypoints, curr_lat, curr_lng)

                # This stores the distances - higher score if you are closer
                place_distances[curr_place] =  1 / curr_distance
        
    final_rst = {} # Mapping of place to final score -- including distance
    for k in place_scores_and_counts:
        if 1/place_distances[k] > max_dist:
            continue
        final_rst[k] = {}
        score = place_scores_and_counts[k][0]
        count = place_scores_and_counts[k][1]
        
        # TODO: Include distance in our score -- place_distances[k] -- in some way
        
        
        final_rst[k]['score'] = (place_distances[k]*score / count)
        final_rst[k]['lat'] = places_to_details[k]['lat']
        final_rst[k]['long'] = places_to_details[k]['lng']
        final_rst[k]['address'] = places_to_details[k]['address']
        final_rst[k]['rating'] = places_to_details[k]['ratings']
        try:
            final_rst[k]['review'] = places_to_details[k]['reviews'][0]
        except:
            final_rst[k]['review'] = ['No reviews found.']
    
    return sorted(final_rst.items(), key=lambda kv: kv[1]['score'], reverse=True)

    
