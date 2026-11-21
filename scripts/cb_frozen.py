"""Private, CPU-only, source-bound scores for the two CB cohorts and the disjoint blog reference."""
import importlib.util
import json
import os
import sys
import time
import zipfile
from pathlib import Path

from cb_inputs import BASE, BLOG, digest, opening, pin, posts

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT/'.local/nine-channel/tp30-frozen-a'
# Use the execution snapshot shared by the measured channel head and need pack.
plan = json.loads((FROZEN/'plan.json').read_bytes())
if any(pin(FROZEN/'code'/name) != h for name,h in plan['snapshotFiles'].items()):
    raise ValueError('Frozen inference source changed')
sys.path.insert(0, str(FROZEN/'code'))
from tompathy_engine.eval.back_half.resources import benchmark_priority, guard

OUT = BASE/'frozen-b'
PACK = Path('.local/nine-channel/c0-b/rp-need-1')
PACK_ID = 'rp-need-1@3195a406e777a664845b18e3d647b38f09f232430e0509330ffc2cd2ac49bccf'


def read(path):
    return json.loads(path.read_bytes())


def reference(selected, check):
    """Apply the same opening and per-author cap to authors outside the study cohort."""
    if pin(BLOG) != '1dfa6996663515a4baf8c1b71713ce8fe9a314b13778701447e4663bbc64c983':
        raise ValueError('Blog source changed')
    with zipfile.ZipFile(BLOG) as z:
        for m in z.infolist():
            if not m.filename.lower().endswith('.xml'):
                continue
            author = Path(m.filename).name.split('.', 1)[0]
            if not author.isdecimal():
                raise ValueError('Missing author ID')
            if author in selected:
                continue
            check()
            ordered = sorted(posts(z.read(m)), key=lambda r: digest(f'TP43:post:{author}:{r[0]}'))
            for ordinal, day, raw in ordered[:40]:
                text = opening(raw)
                if text:
                    yield dict(id=digest(f'TP43:post:{author}:{ordinal}'), text=text,
                               author=digest('TP43:23:'+author), date=day)


def run(check):
    import numpy as np
    from scipy.special import expit
    from tompathy_engine.packs.run import encoder_for
    from tompathy_engine.packs.v2 import load_pack
    from tompathy_engine.eval.readers.encoders import load_encoder
    from tompathy_engine.eval.readers.tp30 import predict
    from tompathy_engine.eval.back_half.reporting import save_json
    pack = load_pack(PACK)
    if pack.pin != PACK_ID or pin(FROZEN/'receipt.json') != 'd04658e1c84ef10e0c95847947359b24da91b79368bd91b3fa22da2d70c3e250':
        raise ValueError('Frozen reader changed')
    receipt = read(FROZEN/'receipt.json')
    inv = FROZEN/'artifact-manifest.json'
    name = 'go_plus_envent-profile-head.npz'
    if pin(inv) != receipt['artifactsPin'] or pin(FROZEN/name) != read(inv)['files'][name]:
        raise ValueError('Frozen profile head changed')
    tags = encoder_for(pack)
    channels, identity = load_encoder(Path('.local/readers/models/minilm'), 'minilm', cap=128)
    if identity['files'] != receipt['vectors']['encoder']['files']:
        raise ValueError('Channel encoder changed')
    with np.load(FROZEN/name) as data:
        head = tuple(data[k] for k in ('parameters','active','constants','supported','iterations'))
    cfg = read(BASE/'registration.json')
    if cfg['inputPin'] != pin(BASE/'inputs.json'):
        raise ValueError('CB roster manifest differs')
    manifest = read(BASE/'inputs.json')
    sources = [('blogs', 'blogs.json', manifest['blogs']['posts']),
               ('isear', 'isear.json', manifest['isear']['reports'])]
    binding = dict(needPack=pack.pin, channelHead=pin(FROZEN/name), channelReceipt=pin(FROZEN/'receipt.json'),
                   inputs=cfg['inputPin'], code=pin(Path(__file__)), samplingCode=pin(Path(__file__).with_name('cb_inputs.py')))
    save_json(OUT/'binding.json', binding)
    counts = {}
    def score(group, rows):
        from itertools import batched
        folder = OUT/group
        folder.mkdir(exist_ok=True)
        n = 0
        for batch in batched(rows, 128):
            check()
            ids = [r['id'] for r in batch]
            texts = [r['text'] for r in batch]
            y = expit(np.asarray(tags(texts)) @ pack.weights.T + pack.bias)
            c = predict(head, channels(texts), 'sigmoid')
            values = np.column_stack((y,c))
            if values.shape != (len(batch),28) or not np.isfinite(values).all():
                raise ValueError('Invalid frozen output')
            path = folder/f'{n:07d}.npz'
            with path.open('xb') as stream:
                np.savez_compressed(stream, ids=np.asarray(ids), values=values)
            n += len(batch)
            save_json(OUT/'progress.json', dict(group=group, rows=n))
        counts[group] = n
    for group, name, expected in sources:
        if pin(BASE/name) != expected:
            raise ValueError('Changed roster '+name)
        score(group, read(BASE/name))
    if pin(BASE/'selected.json') != manifest['blogs']['chosen']:
        raise ValueError('Selected authors changed')
    score('reference', reference(set(read(BASE/'selected.json')), check))
    save_json(OUT/'complete.json', dict(counts=counts, binding=binding))


def main():
    benchmark_priority(2)
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    from tompathy_engine.eval.back_half.reporting import save_json
    spec = importlib.util.spec_from_file_location('counted', ROOT/'scripts/engine-two-day-job.py')
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    def stop():
        if any(p.exists() for p in (BASE/'STOP', BASE.parent/'STOP', Path('.local/word-table/STOP'), OUT/'STOP')):
            raise RuntimeError('Owner stop')
    # The existing local dispatcher owns both priority cards.
    while not (Path('.local/word-table/tp39-change-a/exit-verification.json').is_file() and
               Path('docs/exchange/result-sheets/TP39-change.md').is_file()):
        stop()
        time.sleep(60)
    OUT.mkdir(exist_ok=False)
    from datetime import datetime
    original = datetime.fromisoformat(read(BASE/'frozen/owner.json')['at']).timestamp()
    deadline = time.monotonic()+original+8*3600-time.time()
    def check():
        stop()
        guard()
        if time.monotonic() >= deadline:
            raise RuntimeError('Eight-hour frozen scoring bound')
    try:
        with counted.lease(Path('E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line'), OUT, card='ToMpathy-CB-frozen'):
            check()
            run(check)
    except Exception as exc:
        save_json(OUT/'failed.json', dict(error=str(exc)))
        raise


if __name__ == '__main__':
    main()
