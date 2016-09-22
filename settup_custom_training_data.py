import solr
from math import log
from PIL import Image
import requests
from StringIO import StringIO
import os
import threading
TRAIN_DATA_DIR = '/Users/saurabhjain/tensorflow/custom_corpus'

s = solr.SolrConnection('http://solr-prod.s-9.us:8983/solr/shoprunner')
start = 0
iteration = -1
category_to_image_map = {}
MAX_PER_CATEGORY = 1000

results = s.query('*:*', fields=['image_url', 'category'], rows=20000000).results
image_sets = [(x['image_url'], x['category']) for x in results]
count = 0

for image_set, category in image_sets:
    category = category.split('|')[-1]
    if not category:
        continue
    count += 1
    if not category_to_image_map.get(category):
        category_to_image_map[category] = []
    if len(category_to_image_map[category]) > MAX_PER_CATEGORY:
        continue

    # has all resolutions. we pick the biggest one for best match (hopefully?)
    best_match_image_url = None
    for image in image_set:
        if image.startswith('original|'):
            best_match_image_url = image[9:]
            break
    if not best_match_image_url:
        continue
    category_to_image_map[category].append(best_match_image_url)
    if count % 1000 == 0:
        print count

for category, image_urls in category_to_image_map.items():
    directory_path = TRAIN_DATA_DIR + '/%s' % category
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    image_label_count = 0
    for image_url in image_urls:
        image_label_count += 1
        response = requests.get(image_url)
        img = Image.open(StringIO(response.content))
        image_label = category + '_%s.jpg' % image_label_count
        img.save(directory_path + '/%s' % image_label)
