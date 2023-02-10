import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import requests
import json
import re, random

#Named Entity Recognition (NER)
from nltk import word_tokenize, pos_tag, ne_chunk

#Keyphrase extraction
from nltk.tokenize import sent_tokenize #,word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder

#nltk.download("stopwords")
#nltk.download("punkt")
#nltk.download('averaged_perceptron_tagger')
#nltk.download('maxent_ne_chunker')
#nltk.download('words')

# TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer

# Kobold

api_server = "http://bore.pub:37159"

sampler_order = [6,0,1,2,3,4,5]
prompt="User: What is the meaning to life?"

this_settings = { 
    "prompt": prompt + "\nYou: ",
    "use_story": False,
    "use_memory": False,
    "use_authors_note": False,
    "use_world_info": False,
    "max_context_length": 1600,
    "max_length": 50,
    "rep_pen": 1.08,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 1.0,
    "tfs": 0.9,
    "top_a": 0,
    "top_k": 20,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": sampler_order
}

api_server += "/api"
headers = {"Content-Type": "application/json"}

# Functions

#Part-of-Speech (POS)
def extract_keywords_POS(text):
    tokens = nltk.word_tokenize(text)
    pos_tagged_tokens = nltk.pos_tag(tokens)
    keywords = [word for word, pos in pos_tagged_tokens if pos in ['NN', 'JJ']]
    return keywords

def extract_keywords(text):
    # Tokenize the sentence into words
    words = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = [word for word in words if word.lower() not in stop_words]

    # Return keywords
    return words

#Named Entity Recognition (NER)
def extract_entities(text):
    entities = []
    for chunk in ne_chunk(pos_tag(word_tokenize(text))):
        if hasattr(chunk, 'label'):
            entities.append((chunk.label(), ' '.join(c[0] for c in chunk)))
    return entities

#Keyphrase extraction
def extract_keyphrases(text):
    # Tokenize the text
    tokens = nltk.word_tokenize(text)
    
    # Remove stop words
    stop_words = set(stopwords.words("english"))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Compute bigram measures
    bigram_measures = BigramAssocMeasures()
    
    # Create bigram finder
    finder = BigramCollocationFinder.from_words(tokens)
    
    # Compute the bigrams and scores
    bigrams = finder.nbest(bigram_measures.raw_freq, 10)
    
    return bigrams

# TF-IDF 
def keyword_tfidf(text):
    tokens = nltk.word_tokenize(text)
    pos_tags = nltk.pos_tag(tokens)
    keywords = [word for word, pos in pos_tags if pos.startswith("NN") or pos.startswith("JJ")]
    
    vectorizer = TfidfVectorizer()
    tfidf_weights = vectorizer.fit_transform([text]).toarray()[0]
    tfidf = dict(zip(vectorizer.get_feature_names_out(), tfidf_weights))
    
    return [(keyword, round(tfidf[keyword], 2)) for keyword in keywords if keyword in tfidf]

##################################

response = requests.post(api_server+"/v1/generate", json=this_settings, headers=headers)
response_text = response.json()['results'][0]['text']
response_lines = response_text.split("\n")
for x in range(0, len(response_lines)):
    if response_lines[x].split(":")[-1] != '':
        response_text = response_lines[x].split(":")[-1]
        break
print(response_text)

keywords = extract_keywords(response_text)
print(f"Keywords: {keywords}\n")
keywords = extract_keywords_POS(response_text)
print(f"Part-of-Speech (POS): {keywords}\n")
keywords = extract_entities(response_text)
#response_text += " Overwatch"
#print(f"Named Entity Recognition (NER): {keywords}\n")
#keywords = extract_keyphrases(response_text)
#print(f"Keyphrase extraction: {keywords}\n")
keywords = keyword_tfidf(response_text)
print(f"TF-IDF: {keywords}\n")


