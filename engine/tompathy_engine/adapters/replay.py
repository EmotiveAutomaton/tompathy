# Ported from Sounding Line, copyright 2026 Abraham Haskins (MIT).
# See engine/NOTICE-SOUNDING-LINE.txt and reference-sources.json.
"""Versioned terminal projection of the reviewed Stage 9 replay.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6. NULL: distinct histories with the
same artifact remain indistinguishable in public evidence. ALTERNATIVE:
verified selections and edits preserve native labels and exact episode ends.
Malformed deltas exclude the session; malformed correspondence excludes the
episode. No inferred review/endorsement. Fixtures establish exactness; real
source consistency is not independent final-document validation.
"""
from collections import Counter
import json
from .quill import units, text_of, apply_delta, suggestions


def terminal_spans(document, owners, owner):
    spans=[]; start=None
    for i in range(len(owners)+1):
        retained=i<len(owners) and owners[i]==owner
        if retained and start is None: start=i
        if not retained and start is not None:
            spans.append(dict(start=len(text_of(document[:start])),
                              end=len(text_of(document[:i])),
                              text=text_of(document[start:i]), operation='verified model insertion',
                              support='exact surviving insertion', uncertainty='recorded'))
            start=None
    return spans


def replay(lines, *, retention=False):
    document, provenance, decisions = [], [], []
    active = None
    pending = False
    initialized = False
    failures, semantics, event_counts = Counter(), Counter(), Counter()
    previous_event_num = None
    n_events = n_deltas = 0

    def finish(cutoff):
        nonlocal pending
        if active is not None:
            if active['decision'] is None:
                active['decision'] = 'ignore'
            if pending:
                active['exclusion'] = 'selected suggestion lacks a verified insertion'
            active['end_document'] = text_of(document)
            active['cutoff_ordinal'] = cutoff
            active['terminal_spans'] = terminal_spans(document, provenance, active['ordinal'])
            active['review'] = 'unknown'
            active['endorsement'] = 'unknown'
        pending = False

    for ordinal, raw in enumerate(lines):
        n_events += 1
        try:
            event = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(event, dict):
                raise ValueError('non-object event')
            name = event.get('eventName', '')
            event_counts[name] += 1
            number = event.get('eventNum')
            if number is not None:
                if type(number) is not int or (previous_event_num is not None and number <= previous_event_num):
                    raise ValueError('non-increasing recorded event order')
                previous_event_num = number
            if name == 'system-initialize':
                if initialized:
                    raise ValueError('repeated document initialization')
                document = units(event.get('currentDoc')); provenance = [None] * len(document)
                initialized = True
                continue
            if not initialized:
                raise ValueError('event before document initialization')
        except (ValueError, TypeError, UnicodeError, KeyError) as exc:
            failures[str(exc)] += 1
            continue

        # Suggestion correspondence and document reconstruction are separate
        # measurements. A correspondence failure MUST NOT skip a valid edit.
        try:
            if name == 'suggestion-open':
                finish(ordinal)
                active = {'ordinal': ordinal, 'document': text_of(document),
                          'options': [], 'decision': None, 'selected_index': None,
                          'matched_option_indices': [], 'logged_index_agrees': None,
                          'exclusion': None, 'reopens': 0, 'verified_insertion': False}
                decisions.append(active)
                active['options'] = suggestions(event.get('currentSuggestions'))
            elif name == 'suggestion-reopen':
                if active is None or active['decision'] not in (None, 'dismiss'):
                    raise ValueError('reopen has no unselected suggestion set')
                if suggestions(event.get('currentSuggestions')) != active['options']:
                    raise ValueError('reopen changes offered alternatives')
                active['decision'] = None; active['reopens'] += 1
            elif name == 'suggestion-select':
                if active is None or active['decision'] is not None:
                    raise ValueError('selection has no active undecided set')
                active['decision'] = 'accept'
                active['selected_index'] = event.get('currentSuggestionIndex')
                pending = True
            elif name == 'suggestion-close':
                if active is not None and active['decision'] is None:
                    active['decision'] = 'dismiss'
        except (ValueError, TypeError, UnicodeError, KeyError) as exc:
            semantics[str(exc)] += 1
            if active is not None:
                active['exclusion'] = str(exc)

        delta = event.get('textDelta')
        if delta not in ('', None):
            n_deltas += 1
            before, previous_provenance = text_of(document), provenance
            watched = (active['ordinal'] if active is not None and active['decision'] == 'accept'
                       and event.get('eventSource') == 'user' else None)
            try:
                document, provenance, edited = apply_delta(document, provenance, delta, watched_owner=watched)
            except (ValueError, TypeError, UnicodeError, KeyError) as exc:
                failures[str(exc)] += 1
                continue
            if pending:
                after = text_of(document)
                matches = [o for o in active['options'] if before.endswith('\n') and after ==
                    before[:-1] + o['original'].replace('\r\n','\n').replace('\r','\n') + '\n']
                if event.get('eventSource') == 'api' and matches:
                    active['verified_insertion'] = True
                    active['matched_option_indices'] = [o['index'] for o in matches]
                    active['logged_index_agrees'] = active['selected_index'] in active['matched_option_indices']
                    # Quill can shift an existing terminal newline across a delta's
                    # insertion span. Tag the full verified document transform.
                    count = len(document) - len(previous_provenance)
                    provenance = previous_provenance[:-1] + [active['ordinal']] * count + previous_provenance[-1:]
                    assert len(provenance) == len(document)
                else:
                    active['exclusion'] = 'selected API insertion does not match an offered full-document transform'
                    semantics[active['exclusion']] += 1
                pending = False
            elif edited:
                active['decision'] = 'edit'
    finish(n_events)
    reconstructed = initialized and n_deltas > 0 and not failures
    for row in decisions:
        row['usable'] = reconstructed and row['exclusion'] is None
    result = {'events': decisions, 'events_count': n_events, 'event_counts': dict(event_counts),
            'deltas': n_deltas, 'errors': dict(failures), 'semantic_errors': dict(semantics),
            'reconstructed': reconstructed,
            'final_document': text_of(document), 'final_utf16_length': len(document),
            'decision_counts': dict(Counter(r['decision'] for r in decisions))}
    if retention:
        # Optional ToMpathy outcome export. Default reference replay output is
        # unchanged. These are surviving original UTF-16 units, not quality,
        # review, semantic importance or endorsement judgments.
        counts = Counter(owner for owner in provenance if owner is not None)
        result['session_retained_units'] = dict(counts)
    return result
