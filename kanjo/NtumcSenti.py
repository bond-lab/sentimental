import sqlite3
from collections import defaultdict as dd
from scipy.stats.stats import pearsonr, spearmanr
import numpy as np

latexdir = 'latex/'
db = "/var/www/ntumc/db/eng.db"
MicroWNfile = 'data/Micro-WNop-WN3.txt'

phase1  = [(10000, 10598),  # SPEC
           (11000, 11607) ]  # DANC

phase2 = [ (45681, 46691),  # HOUND
           (46692, 47487),  # HOUND
           (55657, 56209),  # REDH
           (50804, 51464)]  # SCAN
phase3 = [ (47488, 48504),  # HOUND
           (48505, 49505),  # HOUND
           (18525, 18935),  # FINA
           (13147, 13968),] # NAVA
docs = phase1 + phase2 + phase3

corpus = {'Phase1':phase1,
       'Phase2':phase2,
       'Phase3':phase3,
       'NTUMC':docs }
       
conn =  sqlite3.connect(db)
c = conn.cursor()

senti =dd(list)


##
## read eval data
##


def read_MicroWN(filename):
    """
    Read in the wordnet and link it to a filename
    """
    senti= dict()
    fh = open(filename)
    for l in fh:
        if l.startswith('#'):
            continue
        things = l.strip().split('\t')
        of = things[-1]
        score = sum(float(s) for s in things[:-1:2]) #positive
        score += - sum(float(s) for s in things[1:-1:2]) #negative
        score = score / len(things[:-1:2])
        tag=f"{of[1:]}-{of[0]}"
        senti[tag] = score
    return senti

def eval_senti(test, gold, method='Pearson', threshold= 0.05):
    """
    compare two dictionaries of synsets with scores
    calculate Pearson's r for all synsets in both
    return r, signifigance, overlap, nonzero, high_score
    """
    assert(method in  ["Pearson",
                       'Spearman']), f'Unknown Method {method}'
    gl = []
    tl = []
    nz = int()
    hs = int()
    for syn in gold:
        if syn in test:
            gl.append(gold[syn])
            tl.append(test[syn])
            ##print(syn, gold[syn], test[syn])
            if gold[syn] != 0:
                nz += 1
            if abs(gold[syn]) > threshold:
                hs += 1
    if method == 'Spearman':
        r, sig = spearmanr(gl, tl)
    else:
        r, sig = pearsonr(gl, tl)
    return r, sig, len(tl), nz, hs

micro = read_MicroWN(MicroWNfile)



def summarize_corpora(corpus, threshold=0.05):
    stats = dd(lambda: dd(int))
    for name, docs in corpus.items():
        scores = dd(lambda: dd(float))
        senses = dd(lambda: dd(list))
        conceptss = dd(list)
        meanconcepts = dd(float)
        for  (minsid, maxsid) in docs:

            ### Sentences
            c.execute("""select count(sid) from sent 
            WHERE sid >= ? AND sid <= ?""", (minsid, maxsid))
            (sentences,) = c.fetchone()
            #print (name, sentences)
            stats[name]['sents'] += sentences

            ### Words
            c.execute("""select count(wid) from word 
                 WHERE sid >= ? AND sid <= ?""", (minsid, maxsid))
            (words,) = c.fetchone()
            stats[name]['words'] += words

            ### Concepts
            c.execute("""select count(cid) from concept 
            WHERE tag NOT IN ('x', 'e') AND sid >= ? AND sid <= ?""", (minsid, maxsid))
            (concepts, ) = c.fetchone()
            stats[name]['concepts'] += concepts

            c.execute("""SELECT sid, cid, score FROM sentiment
            WHERE sid >= ? AND sid <= ?""", (minsid, maxsid))
            for (sid, cid, score) in c:
                scores[sid][cid] = score
                if score > threshold:
                    stats[name]['positive'] += 1
                elif score < threshold:
                    stats[name]['negative'] += 1
            ### concepts
            c.execute("""SELECT sid, cid, tag, clemma 
            FROM concept WHERE sid >= ? AND sid <= ?""", (minsid, maxsid))
            for (sid, cid, tag, clemma) in c:
                if tag in['x', 'w', 'e']:
                    continue
                senses[tag][clemma].append(scores[sid][cid])
                conceptss[tag].append(scores[sid][cid])
            for tag in conceptss:
                meanconcepts[tag] = np.mean(conceptss[tag])
        stats[name]['distinct'] = len(conceptss)   
        stats[name]['dpos'] = sum(1 for x in conceptss if sum(conceptss[x]) > threshold)
        stats[name]['dneg'] = sum(1 for x in conceptss if sum(conceptss[x]) < -threshold)
        pr, psig, poverlap, pnz, pls = eval_senti(meanconcepts, micro)
        stats[name]['pr'] =pr
        stats[name]['poverlap'] =poverlap
        
    #         print (sid, cid, tag, clemma, scores[lang][sid][cid], sep='\t')
    with open(latexdir + 'tab-ntumc-sum.tex', 'w') as f:
        print("\\begin{tabular}{lrrrrrrrrcr}",
              file=f)
        print(" Corpus & Sentences & Words & Concepts & Distinct & Pos. & Neg. & D Pos & D Neg. & $\\rho$ & Overlap \\\\ \\hline",
              file=f)
        for name in stats:
            if name == 'NTUMC':  ### make a slight space here
                print ("\\\\[-2.0ex]",
              file=f)
            print(name,
                  f"{stats[name]['sents']:,d}",
                  f"{stats[name]['words']:,d}",
                  f"{stats[name]['concepts']:,d}",
                  f"{stats[name]['distinct']:,d}",
                  f"{stats[name]['positive']:,d}",
                  f"{stats[name]['negative']:,d}",
                  f"{stats[name]['dpos']:,d}",
                  f"{stats[name]['dneg']:,d}",
                  f"{stats[name]['pr']:.2f}",
                  f"{stats[name]['poverlap']:,d}",
                  sep=' & ', end = '',
              file=f)
            print (' \\\\',
              file=f)
        print("\\end{tabular}",
              file=f)

summarize_corpora(corpus)


def get_senti(name, docs):
    senti =dd(list)
    for (sfrom, sto) in docs:
    ### sentences where something has been marked for sentiment
        c.execute("""SELECT tag, clemma, score 
        FROM concept AS c LEFT JOIN sentiment AS s 
        ON c.sid = s.sid AND c.cid = s.cid 
        WHERE c.SID >= ? and c.SID <= ?
        AND tag not in ('x', 'w', 'e')
        ORDER BY tag""", (sfrom, sto))


        for (tag, clemma, score) in c:
            #print  (tag, clemma, score, sep='\t')
            if score is None: #If no sentiment treat as 0
                score = 0
            senti[(tag, clemma)].append(score)

    tsv = open(f'ntumc-{name}-senti.tsv', 'w')
    for s in senti:
        mean = np.mean(senti[s])
        print(s[0], s[1], mean, senti[s], sep='\t', file =tsv )

for name, docs in corpus.items():
    get_senti(name, docs)
