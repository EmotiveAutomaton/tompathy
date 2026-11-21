"""TP43 amendment CC. Only verified, whole-author Q19 output can supply reader features."""
from bisect import bisect_right
import json
from pathlib import Path

import numpy as np

from cb_inputs import BASE, digest, pin

def read(path):
    return json.loads(path.read_bytes())


def ridge_predict(x, y, test):
    """Standardize from training texts alone. Unit ridge, unpenalized intercept."""
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale == 0] = 1.
    z = (x-mean)/scale
    target_mean = y.mean(axis=0)
    cross = z.T @ z
    cross.flat[::len(cross)+1] += 1.
    beta = np.linalg.solve(cross, z.T @ (y-target_mean))
    return target_mean + ((test-mean)/scale) @ beta


def crossfit(design, raw, owner, ordered_authors):
    """ordered_authors is also the held-out matching roster; alternate its authors by fold."""
    if len(set(ordered_authors)) != len(ordered_authors) or set(ordered_authors) != set(owner):
        raise ValueError('Cross-fit requires the matching roster of whole read authors')
    if raw.shape != (len(owner),8) or len(design) != len(owner) or not np.isfinite(design).all():
        raise ValueError('Invalid text alignment or design')
    folds = {key:i%2 for i,key in enumerate(ordered_authors)}
    report = dict(readAuthors=len(folds), foldSizes=[(len(folds)+1)//2,len(folds)//2],
                  rule='Alternating matching folds. Fit and scale on the opposite authors only.')
    if len(folds) < 200:
        return None, dict(report, status='unavailable: fewer than 200 read authors')
    side = np.array([folds[key] for key in owner])
    valid = np.isfinite(raw).all(axis=1)
    residual = np.full(raw.shape, np.nan)
    for held in (0,1):
        train = valid & (side != held)
        test = valid & (side == held)
        if len(set(owner[train])) < 2:
            return None, dict(report, status='unavailable: insufficient training authors')
        # Even the departure reference used by the fit contains training authors only.
        import pandas as pd
        def training_departures(values):
            frame = pd.DataFrame(values[train])
            grouped = frame.groupby(owner[train])
            return (frame-(frame.sum()-grouped.transform('sum'))/
                    (len(frame)-grouped.transform('count'))).to_numpy()
        held_design = design[test]-design[train].mean(axis=0)
        held_values = raw[test]-raw[train].mean(axis=0)
        residual[test] = held_values-ridge_predict(training_departures(design),
                                                 training_departures(raw),held_design)
    return residual, dict(report, status='adjusted', validTexts=int(valid.sum()))


def verified_q19():
    from tompathy_engine.packs.trigger import FEATURES
    audit = read(BASE.parent/'Q19-transfer-a.json')
    folder = Path(audit['mirror'])
    receipt = read(folder/'receipt.json')
    cfg = read(BASE/'registration.json')
    manifest = read(BASE/'inputs.json')
    if (not audit['nativeExited'] or not audit['priorFlockReleased'] or
        pin(folder/'receipt.json') != audit['sourceReceiptPin'] or
        pin(Path(audit['inventory'])) != audit['inventoryPin'] or
        receipt['job'] != 'Q19' or receipt['owner']['commit'] != cfg['commit'] or
        receipt['status'] not in ('complete','cutoff') or receipt['inputPin'] != manifest['blogs']['posts']):
        raise ValueError('Unverified Q19 source')
    for key, path in [('posts','blogs.json'),('boundaries','boundaries.json'),('metadata','blog-meta.json')]:
        if pin(BASE/path) != manifest['blogs'][key]:
            raise ValueError('Blog roster changed')
    roster = read(BASE/'blog-meta.json')
    bounds = read(BASE/'boundaries.json')
    read_count = int(receipt['durableRows'])
    if not 0 <= read_count <= min(30000,len(roster)):
        raise ValueError('Invalid prefix')
    n = bisect_right(bounds,read_count)
    stop = bounds[n-1] if n else 0
    raw = np.full((stop,8), np.nan)
    for i in range(stop):
        row = read(folder/'B'/f'row-{i:06d}.json')
        if (row['index'] != i or row['id'] != roster[i][0] or
            row['binding']['inputPin'] != receipt['inputPin'] or row['binding']['role'] != 'B'):
            raise ValueError('Q19 row or binding mismatch')
        if row['values'] is not None:
            raw[i] = [row['values'][k] for k in FEATURES]
    owner = np.array([r[1] for r in roster[:stop]])
    labels = dict((digest('TP43:23:'+a), a) for a in read(BASE/'selected.json'))
    order = sorted(set(owner), key=lambda key: digest('TP39:fold:'+labels[key]))
    return raw, owner, order, dict(source=audit['sourceReceiptPin'], partialAuthorRows=read_count-stop,
                                  wholeAuthorsWithTexts=len(order))
