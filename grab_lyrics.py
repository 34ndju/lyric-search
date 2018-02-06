from bs4 import BeautifulSoup as bs
import urllib2
import os
import math
import time

from collections import Counter
import metapy

from authentication import Secrets
from pymongo import MongoClient
import lyricwikia #https://github.com/enricobacis/lyricwikia
secrets = Secrets()

links = []
links.append("https://www.azlyrics.com/lyrics/fountainsofwayne/stacysmom.html")
links.append("https://www.azlyrics.com/lyrics/logic/18002738255.html")
links.append("https://www.azlyrics.com/lyrics/panicatthedisco/ladevotee.html")

def get_lyrics(link):
    html = urllib2.urlopen(link)
    soup = bs(html, "html5lib")
    return soup.find("pre", {"id":"lyric-body-text"}).text

def parse_and_count(link):
    tag_suppression = True
    n = 1
    min_token_len = 4
    max_token_len = 30

    lyrics = get_lyrics(link)

    doc = metapy.index.Document()
    doc.content(lyrics)

    tok = metapy.analyzers.ICUTokenizer(suppress_tags= tag_suppression)
    tok = metapy.analyzers.LengthFilter(tok, min=min_token_len, max=max_token_len)
    tok = metapy.analyzers.ListFilter(tok, "lemur-stopwords.txt", metapy.analyzers.ListFilter.Type.Reject)
    tok = metapy.analyzers.Porter2Filter(tok)
    tok = metapy.analyzers.LowercaseFilter(tok)

    tok.set_content(lyrics)
    #tokens = [token for token in tok]

    ana = metapy.analyzers.NGramWordAnalyzer(n, tok)
    ngrams = ana.analyze(doc)

    return ngrams

def write_file(filename, contents):
    file = open(filename, "w")
    file.write(str(contents))
    file.close()

#also does tf idf weighting
def write_dicts(links):

    req_timeout = 2 #seconds
    raw_counts_dir_name = "raw_counts"
    normalized_dir_name = "normalized_counts"

    if not os.path.exists(normalized_dir_name):
        os.mkdir(normalized_dir_name)

    if not os.path.exists(raw_counts_dir_name):
        os.mkdir(raw_counts_dir_name)

    doc_freqs = Counter()
    doc_count = 0
    for link in links:
        try: #metapy bug
            id = link[link.rfind("/")+1:].lower().replace("+","_")
            filename = id + ".txt"

            if filename in os.listdir(raw_counts_dir_name):
                file = open(raw_counts_dir_name + "/" + filename, "r")
                contents = file.read()
                file.close()
                result = eval(contents)
            else:
                result = parse_and_count(link)
                write_file(raw_counts_dir_name + "/" + filename, str(result))

            for token in result:
                doc_freqs[token] += 1
            doc_count += 1

        except:
            continue

        print doc_count
        time.sleep(req_timeout)

    for filename in os.listdir(raw_counts_dir_name):
        print filename
        file = open(raw_counts_dir_name + "/" + filename, "r")
        contents = file.read()
        file.close()

        result = eval(contents)

        for token in result:
            log_int = doc_count / float(doc_freqs[token])
            idf = math.log(log_int)
            result[token] *= idf

        write_file(normalized_dir_name + "/" + filename, str(result))

links = []
links.append("https://www.lyrics.com/lyric/32381346/Panic%21+At+the+Disco/La+Devotee")
links.append("https://www.lyrics.com/lyric/13945900/Panic%21+At+the+Disco/Nine+in+the+Afternoon")

write_dicts(links)


'''
client = MongoClient('mongodb://' + secrets.USERNAME + ':' + secrets.PASSWORD + '@ds117858.mlab.com:17858/news-search')
b = client["articles"]
'''
