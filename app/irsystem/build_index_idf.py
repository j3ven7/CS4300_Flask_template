import csv
import os, sys
import googlemaps
from nltk.tokenize import TreebankWordTokenizer
import numpy as np
import pickle

def trimReviews(initial_reviews):
    initial_reviews = initial_reviews.split("\"")
    unwanted_chars = ["{", "}", ",", "\"", "\'"]
    reviews = initial_reviews
    for entry in reviews:
        if entry in unwanted_chars:
            reviews.remove(entry)
    return reviews

def trimTypes(initial_types):
    initial_types = initial_types.split(",")
    types = initial_types
    # Remove curly brace from first and last entry
    types[0] = types[0][1:]
    types[-1] = types[-1][:-1]
    
    return types

def formatData(places):

    all_reviews       = [] # List of string representations of all reviews
    all_types         = [] # List of string representations of all types
    
    review_to_places  = {} # Dictionary mapping review_id to the corresponding place 
    places_to_details = {} # Places to details about that place
    review_id         = 0
    
    # This gives all our data in the correct format
    for place in places:
        curr_reviews = trimReviews(place['reviews'])
        #curr_types   = trimTypes(place['types'])
        # TODO: (Josh) I think it would be dope
        # if we augmented the types by adding synonyms or similar
        # words to the types - i.e. we should add any plural forms of a word
        # or use stemming to make all the words considered the same
        # 
        # Also might be a good metric to compare the search query words
        # to the types using word embeddings after the fact -- 
        # as of now if our query is "fun family friendly aquatics"
        # we might not get good results related to say aquariums or water parks
        # but if we use word embeddings the results would be solid
        # This would involve using spaCy or some similar library
        # To extract key components from a review (i.e. the root and adjective describing the root)
        # and comparing these to our query (also can use types for this)
        curr_types   = place['types'][1:-1]
        curr_name    = place['name']
        
        place['reviews'] = curr_reviews
        place['types']   = curr_types
        
        places_to_details[curr_name] = place
        
        # we need to store all our reviews to vectorize them
        for review in curr_reviews:
            # This adds the name of the place to the review
            curr_review = review
            curr_review = curr_review + " " + curr_name
            for types in curr_types:
                curr_review = curr_review
            all_reviews.append(curr_review)
            all_types.append(curr_types)
            
            review_to_places[review_id] = curr_name
            review_id += 1
    return [all_reviews, all_types, review_to_places,places_to_details]

def build_inverted_index(reviews, tokenizer=TreebankWordTokenizer()):
    """ Builds an inverted index from the messages.
    
    Arguments
    =========
    
    revies: array
        Contains every review from the scraped google results
    
    Returns
    =======
    
    inverted_index: dict
        For each term, the index contains 
        a sorted list of tuples (doc_id, count_of_term_in_doc)
        such that tuples with smaller doc_ids appear first:
        inverted_index[term] = [(d1, tf1), (d2, tf2), ...]
        
    Example
    =======
    >> test_idx['be']
    [(0, 2), (1, 2)]
    
    >> test_idx['not']
    [(0, 1)]
    
    """
    # DONT FORGET TO SORT BY DOC_ID (i.e.) first argument
    inverted_index = {}
    doc_id = 0 
    
    # Iterate over all toks
    for review in reviews:
        tokens = tokenizer.tokenize(review)
        tmp_d = {}
        # Iterate over all tokens in the document
        for token in tokens:
            # If the token has never been seen before make an entry
            if token not in tmp_d:
                tmp_d[token] = 0
            tmp_d[token] += 1
        
        # Now we iterate over our temporary dict
        # And add entries into our inverted_index
        for k in tmp_d:
            if k not in inverted_index:
                inverted_index[k] = []
            inverted_index[k].append((doc_id, tmp_d[k]))
        
        doc_id += 1
    
    return inverted_index


def compute_idf(inv_idx, n_docs, min_df=5, max_df_ratio=0.8):
    """ Compute term IDF values from the inverted index.
    Words that are too frequent or too infrequent get pruned.
    
    Hint: Make sure to use log base 2.
    
    Arguments
    =========
    
    inv_idx: an inverted index as above
    
    n_docs: int,
        The number of documents.
        
    min_df: int,
        Minimum number of documents a term must occur in.
        Less frequent words get ignored. 
        Documents that appear min_df number of times should be included.
    
    max_df_ratio: float,
        Maximum ratio of documents a term can occur in.
        More frequent words get ignored.
    
    Returns
    =======
    
    idf: dict
        For each term, the dict contains the idf value.
        
    """
    
    idf = {}
    # Iterate over all terms in the inv_idx
    for term in inv_idx:
        # Doc frequency
        DF = len(inv_idx[term]) 
        # Throw term away if in fewer than 10 docs
        if DF > 10:
            # Compute idf for term t 
            IDF_t = np.log2(n_docs/(1 + DF))
            
            # Throw term away if it is in more than max_df_ratio of docs
            if DF / n_docs < max_df_ratio:
                idf[term] = IDF_t
    
    return idf

def compute_doc_norms(index, idf, n_docs):
    """ Precompute the euclidean norm of each document.
    
    Arguments
    =========
    
    index: the inverted index as above
    
    idf: dict,
        Precomputed idf values for the terms.
    
    n_docs: int,
        The total number of documents.
    
    Returns
    =======
    
    norms: np.array, size: n_docs
        norms[i] = the norm of document i.
    """
    # DONT FORGET TO CONVERT TO NUMPY ARRAY
    norms = np.zeros(n_docs)
    
    # Only iterate over valid terms
    for term in idf:
        # This does not change by doc
        curr_idf = idf[term]
        
        for entry in index[term]:
            norms[entry[0]] += (entry[1] * idf[term])**2
    
    # Now normalize each entry 
    for i in range(len(norms)):
        norms[i] = np.sqrt(norms[i])

    return norms

def make_pickle(file):
    cwd = os.getcwd()
    with open(file, mode='r') as f:
        places = list(csv.DictReader(f))
    
    all_reviews, all_types, review_to_places, places_to_details = formatData(places)
    
    treebank_tokenizer = TreebankWordTokenizer()
    inv_idx_reviews = build_inverted_index(all_reviews)
    idf_reviews     = compute_idf(inv_idx_reviews, len(all_reviews))
    doc_norms_reviews = compute_doc_norms(inv_idx_reviews, idf_reviews, len(all_reviews))
    
    inv_idx_types = build_inverted_index(all_types)
    idf_types     = compute_idf(inv_idx_types, len(all_types))
    doc_norms_types = compute_doc_norms(inv_idx_types, idf_types, len(all_types))
    
    pickled_data = [inv_idx_reviews,idf_reviews,doc_norms_reviews,inv_idx_types,idf_types,doc_norms_types,
                    review_to_places, places_to_details]

    with open('pickled_data','wb') as f:
        pickle.dump(pickled_data,f)
    
    
    
    


