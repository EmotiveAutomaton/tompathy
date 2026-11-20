"""Pinned, proposed trigger-table-1. Rules never learn from a served page."""
import re

import numpy as np

CHANNELS = ('C2', 'C3', 'C6', 'C9', 'C8')
FEATURES = ('pleasantness', 'unpleasantness', 'self_responsblt', 'goal_support',
            'social_norms', 'other_responsblt', 'standards', 'suddenness')
TAGS = ('contact', 'order', 'status', 'family', 'approval', 'curiosity', 'tranquility',
        'competition', 'savings', 'indep', 'food', 'health', 'power', 'romance',
        'honor', 'serenity', 'idealism', 'rest', 'belonging')
TAG_MAP = {'curiosity': 'N1', 'order': 'N2', 'savings': 'N2', 'tranquility': 'N2', 'serenity': 'N2',
               'belonging': 'N3', 'family': 'N3', 'contact': 'N3', 'status': 'N4', 'approval': 'N4',
               'power': 'N4', 'competition': 'N4', 'honor': 'N4', 'idealism': 'N5', 'food': 'N6', 'rest': 'N6', 'health': 'N6'}
# November 19 owner ruling; version 1 remains available to pinned old studies.
TAG_MAP_V2 = {**TAG_MAP, 'tranquility': 'N6'}
# Fixed before TP24: a conservative finite-predicate rule, not a learned parser.
# First main clause only; later embedded/modal words do not override its tense.
AHEAD = r"\b(will|shall|would|could|might|may)\b|\b(?:about|going) to\b|\bafraid that\b"
ALREADY = r"\b(?:was|were|had|did|has|have)\b|\b\w+ed\b|\b(?:lost|left|went|felt|got|said|saw|took|broke|died|won)\b"


def tense(text, rules=None):
    if rules is not None and rules != {'ahead': AHEAD, 'already': ALREADY}:
        raise ValueError('Unregistered finite-predicate rules')
    clause = re.split(r'[.!?;]', text.lower().replace('’', "'"), maxsplit=1)[0].strip()
    # Initial subordinate clauses are not the main assertion. Without a comma
    # their boundary is ambiguous, so keep the provisional slot unclear.
    if re.match(r'^(?:if|when|because|although|while|unless|until|before|after)\b', clause):
        if ',' not in clause:
            return 'any'
        clause = clause.split(',', 1)[1]
    clause = re.split(r'\b(?:but|and then)\b', clause, maxsplit=1)[0]
    clause = re.sub(r"\bwon't\b", 'will not', clause)
    clause = re.sub(r"\bcan't\b", 'can not', clause)
    clause = re.sub(r"\b(i|you|we|they)'ll\b", r'\1 will', clause)
    clause = re.sub(r"\b(i|you|we|they)'ve\b", r'\1 have', clause)
    words = re.findall(r"[a-z]+", clause)
    past = {'was', 'were', 'did', 'had', 'lost', 'left', 'went', 'felt', 'got',
            'said', 'saw', 'took', 'broke', 'died', 'won', 'knew', 'thought',
            'gave', 'made', 'came', 'found', 'became', 'ran', 'met', 'heard'}
    participles = past | {'been', 'gone', 'seen', 'taken', 'broken', 'known', 'given', 'done', 'written'}
    for i, word in enumerate(words):
        tail = words[i+1:i+6]
        if word in {'will', 'shall', 'would', 'could', 'might', 'may'}:
            return 'ahead'
        if word in past:
            return 'already'
        if word in {'am', 'is', 'are', 'has', 'have', 'do', 'does', 'can', 'must', 'should'}:
            # Present possession is not completed perfect. An adjectival -ed
            # complement after present 'be' is not a past finite verb either.
            significant = [w for w in tail if w not in {'not', 'never', 'already', 'just', 'recently'}]
            if word in {'has', 'have'} and significant and (significant[0] in participles or significant[0].endswith('ed')):
                return 'already'
            phrase = ' '.join(tail)
            if word in {'am', 'is', 'are'} and re.search(r'^(?:not )?(?:about to|going to|afraid that)\b', phrase):
                return 'ahead'
            return 'any'
        if word == 'afraid' and tail[:1] == ['that']:
            return 'ahead'
        if len(word) > 4 and word.endswith('ed'):
            return 'already'
    return 'any'


def validate_rules(rules, tags, features):
    if rules.get('version') != 'trigger-table-1' or tags != list(TAGS) or features != list(FEATURES):
        raise ValueError('Unregistered trigger labels or version')
    if rules.get('tense') != {'ahead': AHEAD, 'already': ALREADY}:
        raise ValueError('Tense rules differ from registered rule file')
    if set(rules.get('tag_map', {})) != set(TAG_MAP) or rules['tag_map'] != TAG_MAP:
        raise ValueError('Trigger mapping differs from proposed registered map')
    for name in ('mean', 'scale'):
        a = np.asarray(rules.get(name), float)
        if a.shape != (29,) or not np.isfinite(a).all() or (name == 'scale' and (a <= 0).any()):
            raise ValueError('Trigger requires fixed training-only standardization')
    for name in ('stakes_qualified', 'table_qualified', 'tense_qualified'):
        if not isinstance(rules.get(name), bool):
            raise TypeError('Missing empirical qualification')


def slots(features, need_logits, texts, rules):
    times = [tense(t, rules['tense']) for t in texts]
    values = np.column_stack([features, need_logits,
        np.array([t == 'ahead' for t in times]), np.array([t == 'already' for t in times])])
    return (values-np.asarray(rules['mean']))/np.asarray(rules['scale']), times


def table_scores(z, include_tense=True):
    """Named unit-weight sums; no fitted table coefficients."""
    f = {name: z[:, i] for i, name in enumerate((*FEATURES, *TAGS, 'ahead', 'already'))}
    time = 1 if include_tense else 0
    return np.column_stack([
        f['unpleasantness']+f['suddenness']+f['other_responsblt'],
        f['unpleasantness']+time*f['ahead']+f['tranquility']+f['health']-f['self_responsblt'],
        f['unpleasantness']+time*f['already']+f['family']+f['contact']+f['belonging']+f['romance']-f['self_responsblt']-f['other_responsblt'],
        f['unpleasantness']+f['self_responsblt']+f['social_norms']+f['approval']+f['status'],
        f['unpleasantness']+f['food']+f['health']+f['order']+f['other_responsblt']-f['suddenness'],
    ])


def stakes(features, logits, z, times, mapping):
    result = []
    eligible = [i for i, name in enumerate(TAGS) if name in TAG_MAP]
    for raw, score, standard, when in zip(features, logits, z, times):
        tag = TAGS[eligible[int(np.argmax(score[eligible]))]]
        direction = 'up' if raw[0] > raw[1] else 'down' if raw[1] > raw[0] else 'either'
        own, other = standard[2], standard[5]
        by = 'circumstance' if max(own, other) <= 0 else 'self' if own > other else 'other' if other > own else 'any'
        result.append({'need': TAG_MAP[tag], 'direction': direction, 'by': by, 'when': when, 'mapping': mapping})
    return result
