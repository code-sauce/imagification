import solr
from math import log
from PIL import Image
import requests
from StringIO import StringIO
import threading

BATCH_SIZE = 100


def get_histogram_dispersion(histogram):
    log2 = lambda x:log(x)/log(2)

    total = len(histogram)
    counts = {}
    for item in histogram:
        counts.setdefault(item,0)
        counts[item]+=1

    ent = 0
    for i in counts:
        p = float(counts[i])/total
        ent-=p*log2(p)
    return -ent*log2(1/ent)

def get_bad_images(image_url, doc_id):
    #print 'get_bad_images ', image_url, doc_id
    response = requests.get(best_match_image_url)
    img = Image.open(StringIO(response.content))
    #img = Image.open('/Users/saurabhjain/imagification/images/imagenotfound3.jpg')
    hist = img.histogram()
    dispersion = get_histogram_dispersion(hist)
    if dispersion < 3.5:
        # blank image
        print doc_id,  best_match_image_url, dispersion


s = solr.SolrConnection('http://solr-prod.s-9.us:8983/solr/shoprunner')
start = 0
iteration = -1
while True:
    iteration += 1
    start = iteration * BATCH_SIZE
    results = s.query('*:*', fields=['id', 'image_url'], rows=BATCH_SIZE, start=start).results
    image_sets = [(x['id'], x['image_url']) for x in results]
    count = 0
    workers = []
    print len(image_sets)
    for doc_id, image_set in image_sets:
        count += 1

        # has all resolutions. we pick the biggest one for best match (hopefully?)
        best_match_image_url = None
        for image in image_set:
            if image.startswith('original|'):
                best_match_image_url = image[9:]
                break
        if not best_match_image_url:
            continue
        workers.append(
            threading.Thread(target=get_bad_images, args=(best_match_image_url, doc_id), name='get_%s' % str(doc_id))
            )
        if count % BATCH_SIZE == 0:
            print '%s processed' % count
            for worker in workers:
                try:
                    worker.start()
                except Exception as ex:
                    print doc_id, best_match_image_url, ex
            for worker in workers:
                worker.join()
            workers = []
