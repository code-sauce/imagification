import solr
from PIL import Image
import pytesseract
import requests

PLACEHOLDER_IMAGE_PATH = '/tmp/best_match_image.jpg'
BATCH_SIZE = 1000

s = solr.SolrConnection('http://solr-prod.s-9.us:8983/solr/shoprunner')
start = 0
iteration = -1
while True:
    iteration += 1
    start = iteration * BATCH_SIZE
    results = s.query('*:*', fields=['id', 'image_url'], rows=BATCH_SIZE, start=start).results
    image_sets = [(x['id'], x['image_url']) for x in results]
    for doc_id, image_set in image_sets:
        # has all resolutions. we pick the biggest one for best match (hopefully?)
        best_match_image_url = None
        for image in image_set:
            if image.startswith('original|'):
                best_match_image_url = image[9:]
                break
        if not best_match_image_url:
            continue
        f = open(PLACEHOLDER_IMAGE_PATH, 'wb')
        image_content = requests.get(best_match_image_url).content
        f.write(image_content)
        f.close()
        image_text = pytesseract.image_to_string(Image.open(PLACEHOLDER_IMAGE_PATH))
        if 'not' in image_text.lower() and 'available' in image_text.lower():
            print doc_id, '-', best_match_image_url, '--', image_text

