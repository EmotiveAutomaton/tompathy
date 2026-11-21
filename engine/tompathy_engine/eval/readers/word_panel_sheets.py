"""Build the RD result sheet from an already landed, source-bound aggregate."""
import argparse
import csv
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from ...packs.registry import sha256
from .reporting import OUTPUTS

PANEL_NAMES = {'registered350': 'Registered 350', 'textFresh348': 'Text-fresh 348'}
DISPLAY = {'developmentWinnerB': 'B development winner', 'standards': 'Own standards',
           'social_norms': 'Social norms', 'self_responsblt': 'Own responsibility',
           'other_responsblt': 'Other responsibility'}
RENDERER_PIN = 'ec94fb152293ba49ed5697c95bc92fffb06e93d21c55bcff025c3e174c5f57b9'


def label(value):
    return DISPLAY.get(value, value.replace('_', ' '))


def number(value):
    return 'unavailable' if value is None else f'{value:.3f}'


def difference(row):
    if row['interval'] is None:
        return number(row['difference']) + ' (interval unavailable)'
    low, high = row['interval']
    return f"{number(row['difference'])} [{number(low)}, {number(high)}]"


def sheet_data(result):
    """Keep a complete numeric table beside the compact owner-facing decision table."""
    rows = []
    picture = []
    text = []

    def add(panel, feature, candidate, row, nominated, selected):
        low, high = row['interval'] or (None, None)
        rows.append([panel, feature, candidate, row['reports'], row['commonValid'],
                     row['candidateRho'], row['trainedRho'], row['difference'], low, high,
                     row['requestedDraws'], row['finiteDraws'], nominated, selected])
        if row['interval'] is not None:
            if result['card'] == 'RD2':
                short_name = {'developmentWinnerB':'B', 'mpnet-base':'MPNet',
                              'ModernBERT-large':'ModernBERT'}.get(candidate, candidate)
                short_feature = {'standards':'standards', 'social_norms':'norms'}[feature]
                picture.append([short_name+' / '+short_feature, panel,
                                row['difference'], low, high])
            else:
                picture.append([label(feature), candidate, row['difference'], low, high])

    if result['card'] == 'RD1':
        text += ['# RD1 reader allocation', '',
                 ('Each difference is the reader’s rank correlation with writers minus the trained reader’s '
                  'on the same valid reports. The interval uses 2,000 paired report draws.'), '',
                 '| Feature | A difference, 95% interval | B difference, 95% interval | Selected reader |',
                 '|---|---:|---:|---|']
        for feature, readers in result['rows'].items():
            selected = result['slots'][feature]
            for candidate, row in readers.items():
                add('F1', feature, candidate, row, '', selected == candidate)
            text.append(f"| {label(feature)} | {difference(readers['A'])} | "
                        f"{difference(readers['B'])} | {selected} |")
        human = {'F1': result['human']}
    else:
        text += ['# RD2 standards and social norms', '',
                 'Writers rated how well an event fit their own standards and social norms. We checked which readers came closest on 350 held-out reports, then checked again after removing two repeated texts.', '',
                 'Both views use the same saved forecasts, paired valid reports and 2,000 paired report draws. '
                 'A nomination requires a 95% interval wholly above zero. ' + result['f3Status'], '',
                 '| Candidate | Feature | Registered 350 difference, 95% interval | Text-fresh 348 difference, 95% interval | F2 nomination (350 / 348) | Changed conclusion |',
                 '|---|---|---:|---:|---|---|']
        for candidate, features in result['rows'].items():
            for feature, outcome in features.items():
                full, fresh = (outcome['panels'][key] for key in PANEL_NAMES)
                for key, row in outcome['panels'].items():
                    add(PANEL_NAMES[key], feature, candidate, row, row['namedOnF2'], row['wouldTakeSlot'])
                changes = []
                if outcome['nominationChanges']:
                    changes.append('F2 nomination')
                if outcome['slotConclusionChanges']:
                    changes.append('confirmed slot')
                noms = ' / '.join('yes' if p['namedOnF2'] else 'no' for p in (full, fresh))
                text.append(f"| {label(candidate)} | {label(feature)} | {difference(full)} | "
                            f"{difference(fresh)} | {noms} | {', '.join(changes) or 'none'} |")
        text.extend(['', ('The registered panel has 350 distinct report IDs. The sensitivity panel omits '
                          'the two prespecified text overlaps. Eight candidate comparisons are possible across both features.')])
        for candidate, status in result['trainedArms'].items():
            text.append(f"\n{label(candidate)} — {status.rstrip('.')}.")
        size = result['researchReaderC']
        if size:
            text += ['', '| Reader C comparison | Features at or above B | Six-feature rule |',
                     '|---|---:|---|']
            for key, panel in size['panels'].items():
                verdict = 'passes' if panel['candidateResearchReader'] else 'misses'
                text.append(f"| {PANEL_NAMES[key]} | {panel['atOrAboveB']} of 8 | {verdict} |")
            changed = [label(v) for v in size['featureNamesChanged']]
            text.extend(['', 'Reader C’s research-reader conclusion ' +
                         ('changes' if size['conclusionChanges'] else 'agrees across both panels') + '.',
                         ('The comparison with B changes for ' + ', '.join(changed) + '.' if changed
                          else 'Every feature gives the same C-versus-B conclusion across both panels.'),
                         '', '| Feature | C rho / B rho on 350 | Valid pairs | C rho / B rho on 348 | Valid pairs |',
                         '|---|---:|---:|---:|---:|'])
            full, fresh = (size['panels'][key] for key in PANEL_NAMES)
            for i, feature in enumerate(size['features']):
                text.append(f"| {label(feature)} | {number(full['readerCRho'][i])} / {number(full['readerBRho'][i])} | "
                            f"{full['commonValid'][i]} | {number(fresh['readerCRho'][i])} / {number(fresh['readerBRho'][i])} | "
                            f"{fresh['commonValid'][i]} |")
        else:
            text.extend(['', 'Reader C had no eligible F2 research-reader comparison.'])
        human = {PANEL_NAMES[k]: v for k, v in result['human'].items()}
    text += ['', '| Panel | Feature | Mean single rereader correlation | Estimable rereaders | Five-rereader mean correlation |',
             '|---|---|---:|---:|---:|']
    for panel, features in human.items():
        for feature, ref in features.items():
            text.append(f"| {panel} | {label(feature)} | {number(ref['singleRereaderMean'])} | "
                        f"{ref['estimableRereaders']} of {ref['rereaders']} | {number(ref['meanOfFiveRho'])} |")
    return text, rows, picture


def csv_text(header, rows):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue()


def write_verified(path, content):
    blob = content.encode('utf8')
    if path.exists():
        if path.read_bytes() != blob:
            raise ValueError('A different result sheet already exists')
        return
    with path.open('xb') as target:
        target.write(blob)


def write_sheet(aggregate, job, directory, renderer, *, plot_python=sys.executable):
    result = json.loads(aggregate.read_bytes())
    card = result['card']
    if (card not in ('RD1','RD2') or aggregate.name != OUTPUTS[card]
            or result['sourceReceiptPin'] != sha256(job/'receipt.json')
            or result['status'] not in ('complete','partial') or result['productionAdmission'] is not False):
        raise ValueError('A source-bound RD aggregate is required')
    if sha256(renderer) != RENDERER_PIN:
        raise ValueError('The registered dot-table renderer changed')
    text, rows, dots = sheet_data(result)
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory/f'{card}-comparisons.csv', csv_text(
        ['panel','feature','candidate','reports','common_valid','candidate_rho','trained_rho','difference',
         'low','high','requested_draws','finite_draws','nominated','takes_slot'], rows))
    if dots:
        cells = directory/f'{card}-differences.csv'
        image = directory/f'{card}-differences.png'
        write_verified(cells, csv_text(['row','col','estimate','low','high'], dots))
        if not image.exists():
            temporary = image.with_suffix('.tmp.png')
            subprocess.run([plot_python, str(renderer), str(cells), str(temporary),
                            f'{card} differences in rank correlation with writers'], check=True)
            os.replace(temporary, image)
        text += ['', f'![Signed rank-correlation differences]({image.name})']
    text += ['', result['scope'], '', (f"Evidence ledger {result['ledger']}. "
             f"[Paired estimates and valid counts]({card}-comparisons.csv) · "
             f"[Source-bound aggregate](../../../engine/validation/{aggregate.name}).")]
    write_verified(directory/f'{card}-panel.md', '\n'.join(text)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('aggregate','job','directory','renderer'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--plot-python', default=sys.executable,
                        help='Interpreter containing matplotlib for the supplied renderer')
    args = parser.parse_args()
    write_sheet(args.aggregate, args.job, args.directory, args.renderer, plot_python=args.plot_python)
