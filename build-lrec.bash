##
## prepare the data for the LREC paper
##

pushd kanjo

# pull the sentiment data from the NTUMC
# assumes the corpus is in /var/www/ntumc/db/eng.db
# as the database is not officially release I will check in the tsv files.

#python NtumcSenti.py
#mv ntumc-*.tsv data/.

#
# Link to a wordnet and check the relations
#
python WnSenti.py > WnSenti.log

#
# Buuld the sentimental wordnet
#

python WnExtend.py  

popd
