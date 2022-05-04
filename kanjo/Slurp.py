###
### macros for reading sentiment lexicons
###
from collections import defaultdict as dd
from pathlib import Path

path = Path(__file__).parent

# read each lexicon into a dictionary of sent[word] = score
# normalize to between -1 and 1

def slurp_DAL():
    data = Path(path, 'data/DAL/DictionaryofAffect')
    fh = open(data)
    rawdata = fh.read()
    data = rawdata[893:481772] # ---- to end data
    valence = dict()
    for l in data.splitlines():
        (word, sentiment, activation, imagery) = l.strip().split()
        valence[word] = float(sentiment) - 2
    return valence

def slurp_AFINN():
    data =  Path(path, 'data/AFINN/AFINN-111.txt')
    fh = open(data)
    valence = dict()
    for l in fh:
        (word, sentiment) = l.strip().split('\t')
        valence[word] = int(sentiment) /5.0
    return valence

def slurp_GLAS():
    data =  Path(path,  'data/GLASGOW/13428_2018_1099_MOESM2_ESM.csv')
    fh = open(data)
    valence = dict()
    for l in fh:
        (word, length,
         AROU_M, AROU_SD, AROU_N,
         VAL_M, VAL_SD, VAL_N,
         DOM_M, DOM_SD, DOM_N,
         CNC_M, CNC_SD, CNC_N,
         IMAG_M, IMAG_SD, IMAG_N,
         FAM_M, FAM_SD, FAM_N,
         AOA_M, AOA_SD, AOA_N,
         SIZE_M, SIZE_SD, SIZE_N,
         GEND_M, GEND_SD, GEND_N) = l.strip().split(',')
        if word and word !='Words':
            valence[word] = (float(VAL_M) - 5) /5.0
            # 1--9
    return valence

def slurp_VADER():
    data =  Path('/home/bond/git/vaderSentiment/vaderSentiment/vader_lexicon.txt')
    fh = open(data)
    valence = dict()
    for l in fh:
        (word, sentiment, std, scores) = l.strip().split('\t')
        valence[word] = float(sentiment) /4.0
    return valence

def slurp_WKW (flat=False):
    data =  Path(path,  'data/WKWSCI/WKWSCISentimentLexicon_v1.1.tab')
    pmap = {"adj":"a",
            "adv":"r",
            "conj":"U",
            "det":"a",
            "excl":"x",
            "inter ":"x", # space here!
            "n":"n",
            "prep":"U",
            "pron":"U",
            "unknown":"U",
            "v":"v"}
    
    valence = dd(lambda: dd(float))
    val = dd(float)
    for l in open(data):
        (t, p, s) = l.strip().split('\t')
        if t == 'term':
            continue
        word = t.strip('"')
        pos = pmap[p.strip('"')]
        score = float(s)/3
        valence[word][pos] = score
    if flat:
        for w in valence:
            scores = valence[w].values()
            val[w] = sum(s for s in scores)/len(scores)
        return val
    else:
        return valence

def slurp_SOCAL (flat=False):
    posmap = {'adj':'a',
              "adv":"r",
              "noun":"n",
              "verb":"v"}
    valence = dd(lambda: dd(float))
    val = dd(float)
    for pos, p in posmap.items():
        for l in open(Path(path, 'data/SOCAL', f'{pos}_dictionary1.11.txt')):
            #print(l)
            (w, s) =  l.strip().split('\t')
            score = float(s)/5
            valence[w][p] = score
    if flat:
        for w in valence:
            scores = valence[w].values()
            val[w] = sum(s for s in scores)/len(scores)
        return val
    else:
        return valence

    
def slurp_S140(bigrams=False):
    data = Path(path, 'data/S140/unigrams-pmilexicon.txt')
    fh = open(data)
    valence = dict()
    for l in fh:
        (word, sentiment, pos, neg) = l.strip().split('\t')
        valence[word] = float(sentiment) / 5
    if bigrams:
      data = Path(path, 'data/S140/bigrams-pmilexicon.txt')
      fh = open(data)  
      for l in fh:
          (word, sentiment, pos, neg) = l.strip().split('\t')
          valence[word] = float(sentiment) / 5
    return valence

def slurp_lab (lang='english'):
    datadir = 'labMT/'
    
    assert(lang in  [ "arabic", "chinese", "english", "french",
                      "german", "indonesian", "korean",
                      "portuguese", "russian", "spanish"]
    ),  f'Unknown Language {lang}'

    data = Path(path, f'data/labMT/labMTwords-{lang}.csv')
    with open(data) as f:
        words = [x.strip() for x in f.readlines()]
    data = Path(path, f'data/labMT/labMTscores-{lang}.csv')
    with open(data) as f:
        scores = [(float(x.strip()) -5)/4.0 for x in f.readlines()]
    return dict(zip(words, scores))
