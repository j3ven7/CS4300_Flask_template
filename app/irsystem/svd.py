import numpy as np
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse.linalg import svds
from sklearn.preprocessing import normalize


with open("./app/irsystem/pickled_data_v2","rb") as f:
    inv_idx_reviews,idf_reviews,doc_norms_reviews,inv_idx_types,idf_types,doc_norms_types, review_to_places, places_to_details = pickle.load(f)

documents = []
for place in places_to_details:
    name = places_to_details[place]['name'].lower()
    types = places_to_details[place]['types'].split(',')#.remove('point_of_interest'))
    try:
        types.remove('point_of_interest')
    except:
        pass
    try:
        types.remove('establishment')
    except:
        pass
    categories = ', '.join(types).replace('_',' ')
    text = ' '.join(places_to_details[place]['reviews'])
    documents.append((name, categories, text))
    
vectorizer = TfidfVectorizer(stop_words = 'english', max_df = .7,
                            min_df = 10)
my_matrix = vectorizer.fit_transform([x[2] for x in documents]).transpose()
u, s, v_trans = svds(my_matrix, k=100)

words_compressed, _, docs_compressed = svds(my_matrix, k=40)
docs_compressed = docs_compressed.transpose()

word_to_index = vectorizer.vocabulary_
index_to_word = {i:t for t,i in word_to_index.items()}

words_compressed = normalize(words_compressed, axis = 1)

def closest_words(word_in, k = len(word_to_index)):
    if word_in not in word_to_index: return "Not in vocab."
    sims = words_compressed.dot(words_compressed[word_to_index[word_in],:])
    asort = np.argsort(-sims)[:k+1]
    return [(index_to_word[i],sims[i]/sims[asort[0]]) for i in asort[1:]]

close_words = {}
for word in word_to_index:
    close_words[word] = dict(closest_words(word))
    
pickled_svd = close_words

with open('pickled_svd','wb') as f:
    pickle.dump(pickled_svd,f)


