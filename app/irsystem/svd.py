import numpy as np
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse.linalg import svds
from sklearn.preprocessing import normalize


with open("pickled_data_v2","rb") as f:
    inv_idx_reviews,idf_reviews,doc_norms_reviews,inv_idx_types,idf_types,doc_norms_types, review_to_places, places_to_details = pickle.load(f)
types = ['accounting','airport','amusement','aquarium','art','gallery','atm',
    'bakery','bank','bar','beauty','salon','bicycle','book','bowling','alley','bus','cafe','campground','dealer',
    'rental','repair','car','wash','casino','cemetery','church','city','hall','clothing','convenience',
    'courthouse','dentist','department','doctor','electrician','electronics','embassy','establishment','finance',
    'fire','florist','food','funeral','furniture','gas','geocode','grocery','supermarket','gym','hair','hardware','health',
    'hindu','temple','home','goods','hospital','insurance','jewelry','laundry','lawyer','library','liquor','government',
    'locksmith','lodging','meal','takeaway','mosque','movie','rental','movie','theater','museum','night',
    'club','painter','park','parking','pet','pharmacy','physiotherapist','worship','plumber','police','post','office',
    'real','estate','restaurant','roofing','contractor','school','shoe','store','shopping','mall','spa','stadium',
    'storage','subway','station','synagogue','taxi','train','travel','agency','university','veterinary','zoo'
]
documents = []
for place in places_to_details:
    name = places_to_details[place]['name'].lower()
    curr_types = places_to_details[place]['types'].split(',')#.remove('point_of_interest'))
    try:
        curr_types.remove('point_of_interest')
    except:
        pass
    try:
        curr_types.remove('establishment')
    except:
        pass
    categories = ', '.join(curr_types).replace('_',' ')
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
for word in types:
    rst = closest_words(word)
    if rst != "Not in vocab.":
        close_words[word] = dict(rst)
    
pickled_svd = close_words

with open('pickled_svd','wb') as f:
    pickle.dump(pickled_svd,f)


