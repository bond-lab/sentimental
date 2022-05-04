import WnSenti
import Slurp
import wn
from collections import defaultdict as dd

latexdir = 'latex/'
sentidata = "data/ntumc-NTUMC-senti.tsv"
#wn = wn.Wordnet(lexicon='pwn:3.0')

wnname = 'omw-en'
wnver= '1.4'
wn = wn.Wordnet(lexicon=f'{wnname}:{wnver}')

sc = dd(lambda: dd(dict))  # sentiment for concepts (synsets)
ss = dd(lambda: dd(dict))  # sentiment for senses   (lemmas)

ss['corpus'], sc['corpus'] = WnSenti.load_senti(sentidata)

VADER = Slurp.slurp_VADER()


# for c in sc['corpus']:
#     print (c, sc['corpus'][c])

mincount = 5
minval = .75

for s in sorted([s for s in wn.senses() if s.id not in ss['corpus']],
                key=lambda x: sum(x.counts()),
                reverse=True):
    lem = s.word().lemma()
    frq = sum(s.counts())
    if lem in VADER and (abs(VADER[lem]) > minval or frq > mincount):
        print (VADER[lem], frq, s.id,
               s.synset().definition(),
               sep='\t')
