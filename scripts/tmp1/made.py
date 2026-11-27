"""Construct artificial histories and scores for independent rehearsal, without a source mount."""
import csv
import datetime
import json
from pathlib import Path
import random
import sys

def make(path):
    path.mkdir()
    adjectives = 'red quiet tall blue round bright wide shallow yellow green light heavy narrow wooden grey short neat smooth spotted square golden thin steep deep gentle slow cold brisk firm white'.split()
    nouns = 'bridge tower island orchard ocean planet button table stone basket forest valley meadow cloud garden boat mountain lantern river pond castle branch acorn field spring cove lake candle library beach'.split()
    rng = random.Random(23)
    (path/'excluded_communities.json').write_text(json.dumps(['test_collection']))
    with (path/'traits.csv').open('x',newline='') as traits,(path/'comments.csv').open('x',newline='') as comments:
        t,c = csv.writer(traits),csv.writer(comments)
        t.writerow(['author','Openness','Extraversion','Agreeableness','Conscientiousness','Neuroticism'])
        c.writerow(['author','id','day','community','text'])
        for i in range(48):
            t.writerow([f'person{i}',*[rng.random() for _ in range(5)]])
            for d in range(126 if i<32 else 18):
                j = i%30 if d%3 else rng.randrange(30)
                noun,adj = nouns[j],adjectives[j]
                text = f'Today we drew a {adj} {noun} on the board. Our little group made up a story about it and took turns describing where it would go and what it would see on the way.'
                day = datetime.date(2000,1,1)+datetime.timedelta(days=d)
                c.writerow([f'person{i}',f'{i}-{d}',day,'fiction',text])
            c.writerow([f'person{i}',f'excluded-{i}','2000-01-01','r/TEST_COLLECTION','Excluded fixture.'])

if __name__ == '__main__':
    make(Path(sys.argv[1]))

