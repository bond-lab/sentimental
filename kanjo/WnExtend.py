import wn
import numpy as np
import sys
from collections import defaultdict as dd
from WnSenti import load_senti
from scipy.stats.stats import pearsonr, spearmanr
import Slurp
import yaml
latexdir = 'latex/'
builddir = 'build/'
sentidata = "data/ntumc-NTUMC-senti.tsv"
#wn = wn.Wordnet(lexicon='pwn:3.0')

wnname = 'omw-en'
wnver= '1.4'
wn = wn.Wordnet(lexicon=f'{wnname}:{wnver}')
MicroWNfile = 'data/Micro-WNop-WN3.txt'

tau = 0.05

###
### store the sentiment lexicons in a dictionary of dictionaries
###
sc = dd(lambda: dd(dict))  # sentiment for concepts (synsets)
ss = dd(lambda: dd(dict))  # sentiment for senses   (lemmas)




##
## read eval data
##


def read_MicroWN(wn,wnname,filename):
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
        try:
            ss = wn.synset(id = f'{wnname}-{tag}')
        except:
            try:
                ss = wn.synset(id = f'{wnname}-{tag}'.replace('-a', '-s'))
            except:
                print("MicroWNOp: couldn't find synset for", of, score)
                continue
        senti[ss.id] = score
    return senti

def eval_senti(test, gold, method='Pearson', threshold= tau):
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


micro = read_MicroWN(wn, wnname, MicroWNfile)



def propagate(lsnt, ssnt, method='mean', threshold=tau):
    """ 
    return mean, newonly
    """
    
    new = dd (lambda: dd(float))
    for lid, score in lsnt.items():
        l = wn.sense(id=lid)
        for r in  l.get_related('antonym'):
            new[r.id]['antonym'] = -score
        for sr in ['derivation',
                   'pertainym']:
            for r in  l.get_related(sr):
                new[r.id][sr] = score

    for sid, score in ssnt.items():
        for l in wn.synset(id=sid).senses():
            if l not in lsnt:
                new[l.id]['synonym'] = score  
    if method == 'mean':
        lsnt_new = lsnt.copy() # average everything
    else:
        lsnt_new = lsnt.copy() # keep old, average new

    for lid in new:
        # print (lid,
        #        lsnt[lid] if l in lsnt else None,
        #        new[l],)
        if method == 'mean':
            if lid not in lsnt:
                scores = []
                for sr in new[lid]:
                    scores.append(new[lid][sr])
                lsnt_new[lid] = float(np.mean(scores))
            else:
                scores = []
                for sr in new[lid]:
                    scores.append(new[lid][sr])
                lsnt_new[lid] = float(np.mean(scores))
                
    return lsnt_new



def lsnt2ssnt(lsnt, threshold=tau):
    ssnt = dict()
    senti = dd(list)
    for lid, score in lsnt.items():
        senti[wn.sense(id=lid).synset().id].append(score)
    for s in senti:
        #print(s, senti[s], np.mean(senti[s]))
        ssnt[s] = float(np.mean(senti[s]))
        #print(s, ssnt[s])
    return ssnt

def dump(sdn, builddir=''):
    with open(f'{builddir}{sdn}-concept.yml', 'w') as out:
        yaml.dump(sc[sdn], out, default_flow_style=False)
    with open(f'{builddir}{sdn}-sense.yml', 'w') as out:
        yaml.dump(ss[sdn], out, default_flow_style=False)

def spread(sdn):
    print(f"Propagating over: {sdn}", file=sys.stderr)
    ss[sdn + ' M'] = propagate(ss[sdn], sc[sdn])
    sc[sdn + ' M'] = lsnt2ssnt(ss[sdn + ' M'])
    dump(sdn,builddir)
    #sc[sdn + ' U'] = lsnt2ssnt(ss[sdn + ' U'])


    
#spread('corpus')

#spread('corpus M')

# spread('corpus M M')
# spread('corpus M M M')
# spread('corpus M M M M')
# spread('corpus M M M M M')
# spread('corpus M M M M M M')
# spread('corpus M M M M M M M')
# spread('corpus M M M M M M M')
# spread('corpus M M M M M M M M')
# spread('corpus M M M M M M M M M')

print('Slurping')

VADER = Slurp.slurp_VADER()
#AFINN = Slurp.slurp_AFINN()
GLAS = Slurp.slurp_GLAS()
# WKW_f =  Slurp.slurp_WKW(flat=True)
# SOC_f =  Slurp.slurp_SOCAL(flat=True)
# S140 =  Slurp.slurp_S140()
WKW_p =  Slurp.slurp_WKW(flat=False)
SOC_p =  Slurp.slurp_SOCAL(flat=False)
labMT = Slurp.slurp_lab()
# vader = slurp_VADER('../../../docs/code/en_senti/VADER/vader_lexicon.txt')

def load_active(file):
    sentiment = dict()
    for l in open(file):
        if l.startswith('#'):
            continue
        row = l.strip().split('\t')
        sentiment[row[2]] = float(row[0])
    return sentiment

def make_mono(wn, lexicon, threshold=tau):
    """
    for all monolingual words in wordnet
    add their sentiment score
    FIXME normalize
    """
    lsenti = dict()
    for l in lexicon:
        if len(s := wn.senses(l)) == 1:
                 lsenti[s[0].id] = lexicon[l]
        # for w in wn.words():
        # ### check for monolingual
        # if len(w.senses()) == 1:
        #     if w.lemma() in lexicon:
        #         lsenti[w.senses()[0].id] = lexicon[w.lemma()]
            ### this does worse    
#            else:
#                lsenti[w.senses()[0]] = 0.0
    return lsenti

def make_mono_pos(wn, lexicon, threshold=tau):
    """
    for all monolingual words in wordnet
    add their sentiment score
    FIXME normalize
    """
    lsenti = dict()
    for l in lexicon:
        for p in lexicon[l]:
            if len(ll := wn.senses(l, pos=p)) == 1:
                lsenti[ll[0].id] = lexicon[l][p]
        # for w in wn.words():
        # ### check for monolingual
        # if len(w.senses()) == 1:
        #     if w.lemma() in lexicon:
        #         lsenti[w.senses()[0].id] = lexicon[w.lemma()]
            ### this does worse    
#            else:
#                lsenti[w.senses()[0]] = 0.0
    return lsenti



def average(l1, l2, normalize=False):
    """
    normalize for the first 
    """
    ll = dict()
    b1 = 0
    b2 = 0
    norm = 1.0
    count = 0
    if normalize:
        for l in set(list(l1.keys())).intersection(set(list(l2.keys()))):
            b1 += abs(l1[l])
            b2 += abs(l2[l])
            count +=1
        norm = b1/b2
    #print(f'{norm=} for {count}')   
    for l in set(list(l1.keys()) + list(l2.keys())):
        if l in l1 and l in l2:
            ll[l] = (l1[l] + (norm * l2[l])) /2
        elif l in l1:
            ll[l] = l1[l]
        else:  # l in l2:
            ll[l] = norm * l2[l] 
    return ll


# ##
# ## Word based
# ##
print('vd')
ss['vd'] = make_mono(wn, VADER)
sc['vd'] = lsnt2ssnt(ss['vd'])
# #spread('vd')


ss['gn'] = make_mono(wn, GLAS)
sc['gn'] = lsnt2ssnt(ss['gn'])

ss['lb'] = make_mono(wn, labMT)
sc['lb'] = lsnt2ssnt(ss['lb'])

ss['vd+gn'] = average(ss['gn'], ss['vd'])
# # for c, score in ss['vd+gn'].items():
# #     print (c, score, sep='\t')
sc['vd+gn'] = lsnt2ssnt(ss['vd+gn'])

print('wrd')
ss['wrd'] = average(ss['vd+gn'],  ss['lb'])
sc['wrd'] = lsnt2ssnt(ss['wrd'])
dump('wrd')
# ##
# ## Lemma and POS based
# ##

ss['sc'] = make_mono_pos(wn, SOC_p)
sc['sc'] = lsnt2ssnt(ss['sc'])

ss['wk'] = make_mono_pos(wn, WKW_p)
sc['wk'] = lsnt2ssnt(ss['wk'])



ss['pos'] = average(ss['sc'],  ss['wk'])
sc['pos'] = lsnt2ssnt(ss['pos'])

dump('pos')
print('lex')
ss['lex'] = average(ss['wrd'],  ss['pos'])
sc['lex'] = lsnt2ssnt(ss['lex'])

dump('lex')


spread('lex')
spread('lex M')
spread('lex M M')
spread('lex M M M')
spread('lex M M M M')
spread('lex M M M M M')
spread('lex M M M M M M')
spread('lex M M M M M M M')
spread('lex M M M M M M M M')
spread('lex M M M M M M M M M')
spread('lex M M M M M M M M M M')
spread('lex M M M M M M M M M M M')

# ###
# ### Combine with Corpus
# ###
print('corpus')
ss['corpus'], sc['corpus'] = load_senti(sentidata)

# ss['cp+wrd'] = average(ss['corpus'], ss['wrd'])
# sc['cp+wrd'] = lsnt2ssnt(ss['cp+wrd'])

# ss['cp+pos'] = average(ss['corpus'], ss['pos'])
# sc['cp+pos'] = lsnt2ssnt(ss['cp+pos'])

ss['cp+lex'] = average(ss['corpus'], ss['lex'])
sc['cp+lex'] = lsnt2ssnt(ss['cp+lex'])



spread('cp+lex')
spread('cp+lex M')
spread('cp+lex M M')
spread('cp+lex M M M')
spread('cp+lex M M M M')
spread('cp+lex M M M M M')
spread('cp+lex M M M M M M')
spread('cp+lex M M M M M M M')
spread('cp+lex M M M M M M M M')
spread('cp+lex M M M M M M M M M')
spread('cp+lex M M M M M M M M M M')
spread('cp+lex M M M M M M M M M M')

##
## Not in LREC paper
##

print('active')
ss['active'] = load_active('data/active.tsv')
sc['active'] = lsnt2ssnt(ss['active'])

#ss['vd+active'] = average(ss['vd'], ss['active'])
#sc['vd+active'] = lsnt2ssnt(ss['vd+active'])
print('all')

ss['all'] = average(ss['cp+lex'], ss['active'])
sc['all'] = lsnt2ssnt(ss['all'])
dump('all')

spread('all')
spread('all M')
spread('all M M')
spread('all M M M')
spread('all M M M M')
spread('all M M M M M')
spread('all M M M M M M')
spread('all M M M M M M M')
spread('all M M M M M M M M')
spread('all M M M M M M M M M')
spread('all M M M M M M M M M M')
spread('all M M M M M M M M M M')

names = {
    'active':'Active',
#    'vd+active':'VD+Act',
    'vd':'VADER',    
    'gn':'GLAS',
    'lb':'labMT',    
    'vd+gn ':'',
    'wrd':'WRD',   
    'sc':'SOCAL',
    'wk':'WKW',    
    'pos':'POS',
    'lex':'LEX',
    'corpus':'NTUMC',
    'cp+lex':'CP+LEX',
    'all':'ALL'}


def name(sdn):
    parts = sdn.split()
    if parts[0] in names:
        if len(parts) == 1:
            return f"{names[parts[0]]}"
        elif len(parts) == 2:
            return f"{names[parts[0]]} P"
        else:
            return f"{names[parts[0]]} P$^{{{len(parts)-1}}}$"
    else:
        return None

# spread('cp+vd+gn')
# spread('cp+vd+gn M')
# spread('cp+vd+gn M M')
# spread('cp+vd+gn M M M')
# spread('cp+vd+gn M M M M')


# lv

# methods = {'corpus':ssnt,
#            'corpus mean':ssnt_mean,
#            'corpus update':ssnt_update,
#            'vader mono':svader_mono,
#            'vader mono mean':svader_mean,
#            'vader mono update':svader_update,
#            'c+v mono':sv_m,
#            'c+v mono mean':sv_m_mean,
#            'c+v mono update':sv_m_update}

print(f"""
MicroOpinion has {len(micro):,d} synsets of which {len([s for s in micro if micro[s] != 0.0])} have non-zero sentiment and {len([s for s in micro if abs(micro[s]) > tau])} have an absolute score > {tau}.

""")

with open(f'{latexdir}tab-sense-cmp.tex', 'w') as tab:
    print('\\begin{tabular}{lrrcrr}', file=tab)
    print('Method      ', 'Size', '$\\ne 0$', '$\\rho$', 'Cover', '$\\ne 0$',
          sep=' & ', end = '\\\\ \\hline\n', file=tab)
    for sdn in sc:
        if (nom := name(sdn)):
            #print (sdn, ss[sdn], micro)
            pr, psig, poverlap, pnz, pls = eval_senti(sc[sdn], micro)
            #    sr, ssig, soverlap, snz, sls = eval_senti(sc[sdn], micro, method='Spearman')
            print(f"{nom:12s}",
                  f"{len(ss[sdn]):7,d}",
                  f"{len([s for s in ss[sdn] if ss[sdn][s] != 0.0]):7,d}",
                  f"{pr:.2f}",    f"{poverlap:5,d}",
                  f"{pnz:5,d}",
                  sep=' & ', end = '\\\\\n', file=tab)
    print('\\end{tabular}', file=tab)


