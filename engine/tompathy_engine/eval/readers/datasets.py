"""Explicit public-data intake. Raw text and author identifiers stay private."""
import argparse
import csv
import json
import shutil
import tarfile
from datetime import UTC, datetime
from pathlib import Path

import requests

from ...packs.registry import sha256

ED = 'https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz'
ED_LICENSE = 'https://raw.githubusercontent.com/facebookresearch/EmpatheticDialogues/main/LICENSE'
GE = 'https://storage.googleapis.com/gresearch/goemotions/data/full_dataset/goemotions_{}.csv'
GE_ROOT = 'https://raw.githubusercontent.com/google-research/google-research/master/goemotions/data/'
GE_LICENSE = 'https://huggingface.co/datasets/google-research-datasets/go_emotions/raw/main/README.md'
REPOSITORIES = {
    'empathic-reactions': ('wwbp/empathic_reactions','3ddbf6b35c789f99c930a349f3fc26b4b2d9ae2e',
        ['README.md','data/responses/data/messages.csv'],'cc-by-4.0','README.md','CC BY 4.0'),
    'worry': ('ben-aaron188/covid19worry','7324d50869578589a47781bc1d26123ca48e27c8',
        ['README.md','LICENSE','data_phase_1/files/meta/rwwd_full.csv'],'gpl-3.0','LICENSE','GNU GENERAL PUBLIC LICENSE'),
    'casino': ('kushalchawla/CaSiNo','2f6ed4a6a55110152a7699fbaa8150d6036314be',
        ['README.md','LICENSE','data/README.md','data/casino.json','data/split/README.md',
         'data/split/casino_train.json','data/split/casino_valid.json','data/split/casino_test.json'],
        'cc-by-4.0','LICENSE','Attribution 4.0 International'),
}


def download(url, destination, limit=500_000_000):
    """No overwrite, bounded transfer, preserve incomplete attempt on failure."""
    destination = Path(destination)
    part = destination.with_suffix(destination.suffix+'.part')
    if destination.exists() or part.exists():
        raise ValueError('Preserve existing downloaded attempt')
    size = 0
    with requests.get(url, stream=True, timeout=(20,120)) as response:
        response.raise_for_status()
        with part.open('xb') as stream:
            for block in response.iter_content(1024*1024):
                size += len(block)
                if size > limit:
                    raise ValueError('Public intake exceeds byte limit')
                stream.write(block)
    part.replace(destination)
    return {'url':url, 'bytes':size, 'sha256':sha256(destination)}


def acquire(name, destination):
    root = Path(destination).resolve()
    if not root.is_relative_to(Path('.local').resolve()) or root.exists():
        raise ValueError('Fresh .local directory required')
    if shutil.disk_usage(root.parent).free < 12*1024**3:
        raise RuntimeError('Insufficient disk headroom for intake')
    root.mkdir(parents=True)
    sources={}
    if name == 'empathetic-dialogues':
        sources['LICENSE.txt']=download(ED_LICENSE,root/'LICENSE.txt',100_000)
        if 'Attribution-NonCommercial 4.0' not in (root/'LICENSE.txt').read_text(encoding='utf8'):
            raise ValueError('EmpatheticDialogues license changed')
        sources['source.tar.gz']=download(ED,root/'source.tar.gz')
        # Extract exactly three plain files, never archive paths or symlinks.
        with tarfile.open(root/'source.tar.gz','r:gz') as archive:
            for split in ('train','valid','test'):
                candidates=[m for m in archive.getmembers() if m.name==f'empatheticdialogues/{split}.csv']
                if len(candidates)!=1 or not candidates[0].isfile() or candidates[0].size>150_000_000:
                    raise ValueError('Unexpected archive member')
                with archive.extractfile(candidates[0]) as source, (root/f'{split}.csv').open('xb') as target:
                    shutil.copyfileobj(source,target)
        counts={}
        for split in ('train','valid','test'):
            with (root/f'{split}.csv').open(encoding='utf8',newline='') as stream:
                rows=list(csv.DictReader(stream,quoting=csv.QUOTE_NONE))
            counts[split]={'utterances':len(rows),'situations':len({row['conv_id'] for row in rows}),
                           'labels':len({row['context'] for row in rows})}
        license='cc-by-nc-4.0'
    elif name == 'go-emotions':
        sources['LICENSE-CARD.md']=download(GE_LICENSE,root/'LICENSE-CARD.md',200_000)
        if '- apache-2.0' not in (root/'LICENSE-CARD.md').read_text(encoding='utf8'):
            raise ValueError('GoEmotions license changed')
        for index in (1,2,3):
            filename=f'goemotions_{index}.csv'
            sources[filename]=download(GE.format(index),root/filename)
        for filename in ('train.tsv','dev.tsv','test.tsv','emotions.txt'):
            sources[filename]=download(GE_ROOT+filename,root/filename,25_000_000)
        ids=set()
        count=0
        for index in (1,2,3):
            with (root/f'goemotions_{index}.csv').open(encoding='utf8',newline='') as stream:
                for row in csv.DictReader(stream):
                    ids.add(row['id'])
                    count+=1
        counts={'individual_judgments':count,'unique_comments':len(ids)}
        license='apache-2.0'
    elif name in REPOSITORIES:
        repo,revision,files,license,license_file,license_text=REPOSITORIES[name]
        for filename in files:
            target=root/filename
            target.parent.mkdir(parents=True,exist_ok=True)
            sources[filename]=download(f'https://raw.githubusercontent.com/{repo}/{revision}/{filename}',target)
        if license_text not in (root/license_file).read_text(encoding='utf8'):
            raise ValueError('Public dataset license differs')
        if name=='casino':
            counts={'dialogues':len(json.loads((root/'data/casino.json').read_text(encoding='utf8')))}
        else:
            target=root/(files[-1])
            with target.open(encoding='utf8',newline='') as stream:
                reader=csv.DictReader(stream)
                fields=reader.fieldnames
                counts={'rows':sum(1 for _ in reader),'fields':fields}
    elif name in ('blogs','blogs-mirror'):
        sources['SOURCE.html']=download('https://u.cs.biu.ac.il/~koppel/BlogCorpus.htm',root/'SOURCE.html',100_000)
        if b'non-commercial research' not in (root/'SOURCE.html').read_bytes():
            raise ValueError('Blog corpus research terms differ')
        url=('https://www.cs.biu.ac.il/~koppel/blogs/blogs.zip' if name=='blogs' else
             'https://huggingface.co/datasets/barilan/blog_authorship_corpus/resolve/728947f6c98ade87aa396004440cb3b58f173cb8/data/blogs.zip')
        sources['blogs.zip']=download(url,root/'blogs.zip',400_000_000)
        if sources['blogs.zip']['sha256']!='1dfa6996663515a4baf8c1b71713ce8fe9a314b13778701447e4663bbc64c983':
            raise ValueError('Blog archive differs from published original checksum')
        import zipfile
        with zipfile.ZipFile(root/'blogs.zip') as archive:
            # Count entries only; do not parse demographic filename components.
            counts={'writer_files':sum(not m.is_dir() and m.filename.endswith('.xml') for m in archive.infolist())}
        license='non-commercial-research'
    else:
        raise ValueError('Unregistered corpus')
    intake={'dataset':name,'license_as_read':license,'research_only':license not in {'apache-2.0','cc-by-4.0'},
            'at':datetime.now(UTC).isoformat(),'sources':sources,'counts':counts,
            'files':{p.relative_to(root).as_posix():sha256(p) for p in root.rglob('*') if p.is_file()}}
    if name in REPOSITORIES:
        intake.update(repository=repo,revision=revision)
        if name=='worry':
            intake['releaseRestriction']='GPL repository; keep research-only pending explicit distribution license compatibility review'
    (root/'intake.json').write_text(json.dumps(intake,indent=2)+'\n',encoding='utf8')
    return {k:v for k,v in intake.items() if k not in {'sources','files'}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name',choices=('empathetic-dialogues','go-emotions','blogs','blogs-mirror',*REPOSITORIES))
    parser.add_argument('--directory',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(acquire(args.name,args.directory)))


if __name__=='__main__':
    main()
