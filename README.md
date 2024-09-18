# sentimental
A Sentimental Wordnet

> _Fer when yeh've come to weigh the good an' bad—_
> _The gladness wiv the sadness you 'ave 'ad—_

from [_Songs of a Sentimental Bloke_](https://en.wikisource.org/wiki/The_Songs_of_a_Sentimental_Bloke) by C. J. Dennis


This code makes a sense-based sentiment lexicon for English. It
combines word-level and POS-level lexicons from various sources and a
sense and sentiment tagged corpus (the NTU-MC).  These scores are
propogated across the semantic network using smantic links.

## Results

We include the most useful of the lexicons built:


| Method | Size | non 0 | ρ | Cover | % of 1054 | non 0 | % of 597 | Name in Paper |
|:-------|-----:|------:|--:|------:|----------:|------:|---------:|:--------------|
| [Lexicons](results/lex-sense.yml) | 16,499 | 8,179 | 0.86 | 217 | 20.59% | 153 | 25.63% | LEX |
| [Corpus](results/ntumc-sense.yml) | 11,154 | 2,989 | 0.75 | 339 | 32.16% | 200 | 33.50% | NTUMC |
| [Lexicon+Corpus](results/all-sense.yml) | 26,325 | 10,793 | 0.81 | 471 | 44.69% | 296 | 49.58% | ALL |
| [Propagated](results/best-sense.yaml) | 79,155 | 49,466 | 0.82 | 768 | 72.87% | 467 | 78.22% | ALL P¹¹ |
| SentiWordnet | 117,659 | ? | 0.63 | 1,054 | 100.00% | 597 | 100.00% | |

[Micro-WNOp](https://github.com/aesuli/SentiWordNet?tab=readme-ov-file#micro-wordnet-opinion-10--30) is used for the evaluation. Size is the number of senses in the lexicon; non 0 is the number with non-zero sentiment; ρ is the correlation with Micro-WNOp, and cover is the number of entries in Micro-WNOp found in the lexicon (1,054 possible, with 597 non-zero). We also compare to SentiWordnet.

 * LEX is monosemous words linked to their sentiment in word(+pos)-based hand-built lexicons
 * NTUMC is words marked for sentiment in the [Natural text Understanding Multilingual Corpus](https://github.com/bond-lab/NTUMC)
 * ALL is the combination of these, the best combination of manual resources
 * ALL P¹¹ propogates these through synonym, derivation, pertainym and antonym links 11 times (until it stabilizes). **This is the lexicon we suggest you use**.
 * [Sentiwordnet](https://github.com/aesuli/SentiWordNet?tab=readme-ov-file) is the first sentiment wordnet built by propogation

The format is yaml, with the key being the key in the OMW wordnet derived from PWN 3.0 (omw:1.4) in the [omw-data package](https://github.com/omwn/omw-data) and the value being the sentiment: a float between +1 and -1.

```yaml
omw-en-happy--go--lucky-01998260-s: 0.6666666666666666
omw-en-happy-01148283-a: 0.513
omw-en-happy-02565583-s: 0.505
omw-en-harangue-00990249-v: -0.6666666666666666
omw-en-harassed-02455845-s: -0.625
omw-en-harbinger-00974173-v: 0.0
omw-en-hard--and--fast-02506267-s: 0.0
omw-en-hard--bitten-02448623-s: 0.0
omw-en-hard--line-01026150-s: -0.3333333333333333
omw-en-hard--nosed-01940651-s: -0.1
omw-en-hard--pressed-02457558-s: -0.27
```

## Citation

The process is described in full detail in Bond and Herng (2022)


Francis Bond and Merrick Choo. 2022. [Sense and Sentiment](https://aclanthology.org/2022.lrec-1.7). In Proceedings of the Thirteenth Language Resources and Evaluation Conference, pages 61–69, Marseille, France. European Language Resources Association.

Erata: In Table 9 we say there are 457 non-zero senses in Micro-WNOp, but there are 597 non-zero senses and 457 senses where the score is zero!
