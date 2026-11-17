"""One opt-in runtime for verified sentence readers. Missing packs stay empty."""
from dataclasses import dataclass

import numpy as np

from ..packet.bottom_box import BottomBoxV1, empty_bottom_box
from .aggregate import shares
from .registry import load_pack


@dataclass(frozen=True)
class Sentence:
    text: str
    start: int
    end: int


def encoder_for(pack):
    """Load exclusively from verified local files; never fetch a missing model."""
    m = pack.manifest
    if m.encoder.kind == 'tfidf':
        import json

        from sklearn.feature_extraction.text import TfidfVectorizer
        source = json.loads((pack.root/'encoder/vocabulary.json').read_text(encoding='utf8'))
        vectorizer = TfidfVectorizer(vocabulary=source['vocabulary'],
            ngram_range=tuple(source['ngram']), sublinear_tf=source['sublinear_tf'])
        vectorizer.idf_ = np.asarray(source['idf'], float)
        return lambda texts: vectorizer.transform(texts).toarray()
    import torch
    torch.set_num_threads(2)
    if m.encoder.kind == 'model2vec':
        from model2vec import StaticModel
        model = StaticModel.from_pretrained(str(pack.root / 'encoder'))
        return lambda texts: model.encode(texts, max_length=m.token_cap, show_progress_bar=False,
                                          use_multiprocessing=False)
    if m.encoder.kind == 'sentence-transformers':
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(str(pack.root / 'encoder'), device='cpu',
                                    local_files_only=True, trust_remote_code=False)
        model.max_seq_length = m.token_cap
        return lambda texts: model.encode(texts, batch_size=16, show_progress_bar=False,
                                         normalize_embeddings=True)
    raise ValueError('Constructed encoder requires an explicit test adapter')


def run(directory, sentences, *, enabled=False, encoder=None, check=lambda: None,
        research=False, adapters=None, diagnostics=None):
    if isinstance(directory, (list, tuple)):
        from .runtime import run as current
        return current(directory, sentences, enabled=enabled, research=research,
                       adapters=adapters, check=check, diagnostics=diagnostics)
    box = empty_bottom_box()
    if not enabled:
        return box
    pack = load_pack(directory)
    if pack is None:
        return box
    m = pack.manifest
    rows = list(sentences)
    last = 0
    for row in rows:
        if (not row.text.strip() or row.start < last or row.end <= row.start
                or row.end - row.start != len(row.text.encode('utf-16-le')) // 2):
            raise ValueError('Sentences need ordered, exact UTF-16 spans')
        last = row.end
    if not rows:
        return box
    if encoder is not None and m.encoder.kind != 'constructed':
        raise ValueError('Production encoder cannot be replaced by an unpinned adapter')
    check()
    encode = encoder or encoder_for(pack)
    batches = []
    for start in range(0, len(rows), 16):
        check()
        batches.append(np.asarray(encode([s.text for s in rows[start:start+16]])))
    vectors = np.concatenate(batches)
    if vectors.shape != (len(rows), pack.weights.shape[1]) or not np.isfinite(vectors).all():
        raise ValueError('Encoder returned invalid embeddings')
    logits = vectors @ pack.weights.T + pack.bias
    probabilities = np.exp(logits - logits.max(axis=1, keepdims=True))
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    predictions = probabilities.argmax(axis=1)
    confidence = probabilities.max(axis=1)
    read = confidence >= m.abstention_threshold
    neutral = m.labels.index(m.neutral)
    identifiers = list(dict.fromkeys(m.label_map.values()))
    groups = [[i for i, label in enumerate(m.labels) if m.label_map.get(label) == ident]
              for ident in identifiers]
    estimates = shares(predictions[read], pack.table, pack.policy, neutral=neutral, groups=groups)
    # Many labels may map to one channel. Correct in label space, then combine.
    # Bootstrap grouped shares jointly below rather than summing marginal intervals.
    for group_index, (ident, indices) in enumerate(zip(identifiers, groups)):
        events = [{'span': [s.start, s.end], 'label': m.labels[int(p)], 'confidence': float(c),
                   'who': 'unclear', 'words': []}
                  for s, p, c, accepted in zip(rows, predictions, confidence, read)
                  if accepted and int(p) in indices]
        share = estimates[group_index] if estimates is not None else None
        if events or share:
            box['on_page'].append({'id': ident, 'tier': 'on_page', 'share': share,
                'events': events, 'series': [], 'pack': pack.pin,
                'key': m.key.model_dump(), 'score': m.score.model_dump(),
                'people': m.people, 'floor': m.floor, 'nothing_here': m.nothing_here,
                'mapping': m.mapping.model_dump(), 'status': 'benchmarked'})
    return BottomBoxV1.model_validate(box).model_dump(mode='json', by_alias=True)
