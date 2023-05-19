#!/bin/sh

python -c "import synonyms"
# >> Synonyms load wordseg dict [/usr/local/lib/python3.9/site-packages/synonyms/data/vocab.txt] ... 
# >> Synonyms on loading stopwords [/usr/local/lib/python3.9/site-packages/synonyms/data/stopwords.txt] ...
# >> Synonyms on loading vectors [/usr/local/lib/python3.9/site-packages/synonyms/data/words.vector.gz] ...
# >> Synonyms downloading data from https://gitee.com/chatopera/cskefu/attach_files/610602/download/words.vector.gz to /usr/local/lib/python3.9/site-packages/synonyms/data/words.vector.gz ... 
#  this only happens if SYNONYMS_WORD2VEC_BIN_URL_ZH_CN is not present and Synonyms initialization for the first time. 
python -c "import pycorrector; pycorrector.correct('少先队员因该为老人让坐'); pycorrector.en_correct('falut text')"
# 2023-mm-dd 09:16:25.917 | DEBUG    | pycorrector.detector:_initialize_detector:89 - Loaded language model: /opt/opt/.pycorrector/datasets/zh_giga.no_cna_cmn.prune01244.klm
# 2023-mm-dd 09:16:32.145 | DEBUG    | pycorrector.en_spell:_init:39 - load en spell data: /usr/local/lib/python3.9/site-packages/pycorrector/data/en/en.json.gz, size: 30120

python3 manage.py makemigrations main
python3 manage.py migrate

# python3 manage.py runserver 80
# celery -A GifExplorer worker -l info -n worker1@%h -D --logfile=celery.log & \
celery -A GifExplorer worker -l info -n worker1@%h -c 4 & \
uwsgi --module=GifExplorer.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=GifExplorer.settings \
    --master \
    --http=0.0.0.0:80 \
    # --processes=5 \
    --harakiri=40 \
    --max-requests=5000 \
    --vacuum
