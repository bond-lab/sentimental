###
### Read the output from the ntumc and link it to a wordnet
###
### Evaluate the different relations
###
### by Francis Bond (2021)
###

import wn
from collections import defaultdict as dd
import numpy as np
import sys
import re
latexdir = 'latex/'
sentidata = "data/ntumc-NTUMC-senti.tsv"

#wn.download('https://github.com/omwn/omw-data/releases/download/v1.4/omw-en-1.4.tar.xz')
wn = wn.Wordnet(lexicon='omw-en:1.4')
prefix='omw-en'


def load_senti(data, threshold=0.05, debug=False):
    """
    load the sentiment data
    store it in a dictionary indexed by lemma
    discard if:
       * no lemma is found
       * |score| < threshold 
    return the dictionary
    based on the fact that we know 'omw-en' uses similar IDs as the corpus
    """
    lsentiment = {}
    ssentiment = {}
    senti = dd(list)
    for l in open(data):
        (tag, lemma, score, scores) = l.strip().split('\t')
        score = float(score) / 100
        ## try to find the synset in wordnet
        try:
            ss = wn.synset(id = f'{prefix}-{tag}')
        except:
            try:
                ss = wn.synset(id = f'{prefix}-{tag}'.replace('-a', '-s'))
            except:
                if debug:
                    print("couldn't find synset", tag)
                continue

        if abs(score) > threshold:
            senti[ss.id].append(score)
        else:
            senti[ss.id].append(0.0)
        ### try to find the lemma in wordnet
        senses = set()
        for s in ss.senses():
            #print(s)
            for f in s.word().forms():
                #print(f'{f}')
                #f = f.replace('(a)', '')
                #f = f.replace('(p)', '')
                if f.lower() in [lemma,
                                 lemma.lower(),
                                 lemma.lower().replace('_','-'),
                                 lemma.lower().replace('_',' '),
                                 lemma.lower().replace('_',''),
                                 lemma.lower().replace(' ','-'),
                                 lemma.lower().replace('-',' '),
                                 lemma.lower().replace('-',''),
                                 lemma.lower().replace('-',''),
                                 lemma.lower().replace(' ','')]:
                    senses.add(s)
        #print(f'{senses=}')
        try:
            match = senses.pop()
            #print(f'LEM {len(senses)} {match} {senses}')
        except:
            if debug:
                print(f"couldn't find '{lemma}' in {ss}")
                print ([x.word().lemma() for x in ss.senses()])
            continue
        if abs(score) > threshold:
            lsentiment[match.id] = score
        else:
            lsentiment[match.id] = 0.0
        if len(senses) > 0:
            if debug:
                print(f"multi {senses}")
    for s in senti:
        #print(s, senti[s], np.mean(senti[s]))
        ssentiment[s] = np.mean(senti[s])
    ## return the average sentiment for each lemma,
    ## and for each synset
    #print('LEM len', len(lsentiment))
    return lsentiment, ssentiment




if __name__ == "__main__":
    lsnt, ssnt = load_senti(sentidata, debug=True)

    ##
    ## print our the numbers of senses and sentiments with lemmas
    ##

    with open(f'{latexdir}tab-omw-sum.tex', 'w') as tab1:
        print(f"""
        \\begin{{tabular}}{{lrrrr}}
        & Synsets & Score & Lemmas & Score \\\\ \\hline
        All      & {len(ssnt):,d}   
        & {np.mean([ssnt[s] for s in ssnt]):+.3f}  
        & {len(lsnt):,d}   
        & {np.mean([lsnt[s] for s in lsnt]):+.3f}  
        \\\\
        Non-Zero & {len([s for s in ssnt if ssnt[s] != 0]):,d}
        & {np.mean([ssnt[s] for s in ssnt if ssnt[s] != 0]):+.3f} 
        & {len([s for s in lsnt if lsnt[s] != 0]):,d}   
        & {np.mean([lsnt[s] for s in lsnt if lsnt[s] != 0]):+.3f}  
        \\\\
        Positive & {len([s for s in ssnt if ssnt[s] > 0]):,d}

        & {np.mean([ssnt[s] for s in ssnt if ssnt[s] > 0]):+.3f} 
        & {len([s for s in lsnt if lsnt[s] > 0]):,d} 
        & {np.mean([lsnt[s] for s in lsnt if lsnt[s] > 0]):+.3f}  
        \\\\
        Negative & {len([s for s in ssnt if ssnt[s] < 0]):,d}
        & {np.mean([ssnt[s] for s in ssnt if ssnt[s] < 0]):+.3f} 
        & {len([s for s in lsnt if lsnt[s] < 0]):,d}   
        & {np.mean([lsnt[s] for s in lsnt if lsnt[s] < 0]):+.3f}  
        \\end{{tabular}}
        """, file = tab1)



    max_l_sent = max([lsnt[s] for s in lsnt])
    min_l_sent = min([lsnt[s] for s in lsnt])
    print(f"Most positive senses ({max_l_sent}): {', '. join([wn.sense(l).word().lemma() for l in lsnt if lsnt[l]==max_l_sent])}")
    print(f"Most negative senses ({min_l_sent}): {', '. join([wn.sense(l).word().lemma() for l in lsnt if lsnt[l]==min_l_sent])}")



    ## Take a look at the data
    # for l in lsnt:
    #     if abs(lsnt[l]) > 0.05:
    #         print (l, lsnt[l])
    # for s in ssnt:
    #     if abs(ssnt[s]) > 0.05:
    #         print (s, ssnt[s])

    def synset_diffs(ssnt, relation, nonzero=False):
         """
         find the average difference for all synsets related by the 
         'similar to' relation which have non-zero sentiment
         """
         diffs = []
         ## look at all the synsets we have sentiment for
         for s1 in ssnt:
             ss1=wn.synset(id=s1)
             for ss2 in ss1.get_related(relation):
                 s2 = ss2.id
                 #print (s1, s2)
                 ## look at all synsets similar_to them
                 ## but only in one direction
                 if s1 < ss2.id:
                     continue
                 if (s1 in ssnt) and  (s2 in ssnt):
                     if nonzero and (ssnt[s2] == 0.0  and ssnt[s1] == 0.0):
                         continue
                     diff = (abs(ssnt[s1] - ssnt[s2]))
                     diffs.append(diff)
                     #print (s1, s2, ssnt[s1], ssnt[s2],diff)
                     #print(s1.definition())
                     #print(s2.definition())
         return diffs # or np.mean(diffs)


    # sim_diff = synset_diffs(ssnt, 'similar')
    # print (sim_diff)
    # #syn_diff = synonym_diffs(lsnt)
    # syn_diff = synonym_diffs(lsnt, nonzero=True)
    with open(f'{latexdir}tab-omw-concept.tex', 'w') as tab:
        print('\\begin{tabular}{lrrrr}', file=tab)
        print('Relation  & All & Score & Non-Zero & Score \\\\ \\hline', file=tab)
        for relation in ['similar', 'hyponym', 'holo_location',
                         'holo_member',
                         'holo_part',
                         'holo_portion',
                         'holo_substance',
                         #'holonym',
                         'entails', 'causes', ]:
     # 'mero_location', 'mero_member'
     #                     'mero_part', 'mero_portion', 'mero_substance', 'meronym',
     #    ]:
            withzero = synset_diffs(ssnt, relation)
            withoutzero=synset_diffs(ssnt, relation, nonzero=True)
            print(relation.replace('_', ' '), 
                  f"{len(withzero):,d}", f"{np.mean(withzero):+.3f}", 
                  f"{len(withoutzero):,d}", f"{np.mean(withoutzero):+.3f}", 
                  sep = ' & ', end = '\\\\\n', file=tab)
        print('\\end{tabular}', file=tab)


    ###
    ###
    ###
    def synonym_diffs(lsnt, nonzero=False):
        """
        find the average difference for all lemmas withing the same synset
        """
        diffs = []
        ## look at all the synsets we have sentiment for
        known = set()
        for ln in lsnt:
            l = wn.sense(id=ln)
            try:
                ss = l.synset()
                if ss in known:
                    continue
                else:
                    known.add(ss)
                ### lemmas with sentiment
                lems = [ll for ll in ss.senses() if ll.id in lsnt]
                sdiff = []
                if len(lems) > 1:
                    for l1 in lems:
                        for l2 in lems:
                            if l1 > l2:
                                #print('LEM',l1,l2,lsnt[l1.id],lsnt[l2.id])
                                if nonzero and \
                                   lsnt[l1.id] == 0.0 and lsnt[l2.id] == 0.0:
                                        continue
                                sdiff.append(abs(lsnt[l1.id]-lsnt[l2.id]))
                    if sdiff:
                        diffs.append(np.mean(sdiff))
                    if np.mean(sdiff) > .5:
                        print(ss, np.mean(sdiff), [(x,  lsnt[x.id]) for x in lems])
            except:
                print('WARNING: Weird Key:', l)

        return diffs # or np.mean(diffs)

    def lemma_diffs(lsnt, relation, nonzero=False):
         """
         find the average difference for all synsets related by the 
         'similar to' relation which have non-zero sentiment
         """
         diffs = []
         ## look at all the synsets we have sentiment for
         if relation ==  'ant_opposite':
             opposite = True
             relation =  'antonym'
         else:
             opposite = False
         for l1 in lsnt:
            lm1 = wn.sense(id=l1)
            for lm2 in lm1.get_related(relation):
                 l2=lm2.id  
                 #print (s1, s2)
                 ## look at all synsets similar_to them
                 ## but only in one direction
                 if l1 < l2:
                     continue
                 if (l1 in lsnt) and  (l2 in lsnt):
                     if nonzero and (lsnt[l2] == 0.0  and lsnt[l1] == 0.0):
                         continue
                     if opposite:
                         diff = (abs(lsnt[l1] + lsnt[l2]))
                     else:
                         diff = (abs(lsnt[l1] - lsnt[l2]))
                     diffs.append(diff)
                     #print (relation, l1, l2, lsnt[l1], lsnt[l2], diff, opposite)
                     #print(s1.definition())
                     #print(s2.definition())
         return diffs # or np.mean(diffs)

    with open(f'{latexdir}tab-omw-sense.tex', 'w') as tab:
        print('\\begin{tabular}{lrrrr}', file=tab)
        print('Relation & All & Score & Non-Zero & Score \\\\ \\hline', file=tab)
        ### synonyms
        withzero =  synonym_diffs(lsnt)
        withoutzero=synonym_diffs(lsnt, nonzero=True)
        print ('synonym',
               f"{len(withzero):,d}",
               f"{np.mean(withzero):+.3f}", 
               f"{len(withoutzero):,d}",
               f"{np.mean(withoutzero):+.3f}", 
               sep = ' & ', end = '\\\\\n', file=tab)
        ### relations
        for relation in [
                'antonym',
                'ant_opposite',
                'also',
                'derivation',
                'pertainym']:
            # 'mero_location', 'mero_member'
            # 'mero_part', 'mero_portion',
            # 'mero_substance', 'meronym',
            # 'similar'     ]:
            withzero = lemma_diffs(lsnt, relation)
            withoutzero=lemma_diffs(lsnt, relation, nonzero=True)
            print(relation.replace('_', ' '), 
                  f"{len(withzero):,d}",
                  f"{np.mean(withzero):+.3f}", 
                  f"{len(withoutzero):,d}",
                  f"{np.mean(withoutzero):+.3f}", 
                  sep = ' & ', end = '\\\\\n', file=tab)
        print('\\end{tabular}', file=tab)


    # print(f"Average difference in non-zero sentiment for similar_to {np.mean(sim_diff)}, defined for {len(sim_diff)} pairs")
