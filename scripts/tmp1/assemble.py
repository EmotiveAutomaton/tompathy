"""Assemble only registered model files and the reviewed CPU code in a fresh delivery."""
import ast
import hashlib
import json
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WEEK = REPO / '.local/week-20261122'

def pin(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def selected_source(path, names):
    code = path.read_text(encoding='utf8')
    return '\n\n'.join(ast.get_source_segment(code, node) for node in ast.parse(code).body
                        if isinstance(node, ast.FunctionDef) and node.name in names)

def assemble(folder):
    out = folder / 'payload'
    out.mkdir(parents=True, exist_ok=False)
    cfg = WEEK / 'registration.json'
    assert pin(cfg) == '22e90646c03230dd8c00fe1cb98ff38149adc445467fd11c8050916ca8fcfbb9'
    source = json.loads(cfg.read_bytes())['models']
    wanted = {p for p in source if p in ('tags.npz','worry.npz','channels.npz') or
              p.split('/')[-1] in ('config.json','tokenizer.json','model.safetensors') and p.count('/') == 1}
    assert source['base/model.safetensors'] == source['need/model.safetensors']
    assert source['base/tokenizer.json'] == source['need/tokenizer.json']
    with tarfile.open(WEEK / 'open-inputs-a.tar') as archive:
        for name in sorted(wanted):
            if name.startswith('need/'):
                continue
            path = out / 'models' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile('models/'+name) as src, path.open('xb') as dst:
                shutil.copyfileobj(src,dst)
            assert pin(path) == source[name]
    audit = json.loads((WEEK/'Q21-transfer.json').read_bytes())
    assert audit['nativeExited'] and audit['priorFlockReleased']
    pride = Path(audit['mirror'])/'pride.npz'
    assert pin(pride) == audit['files']['pride.npz'] == 'b28a4354eb385122d2733087318b814271d52af29db976b06a321114fca1973b'
    shutil.copyfile(pride,out/'models/pride.npz')
    forms = json.loads((WEEK/'TP45-profiles-a/receipt.json').read_bytes())['forms']
    (out/'style.json').write_text(json.dumps(forms),encoding='utf8')
    wheels = WEEK/'TP58-build-a/wheels'
    meta = json.loads((wheels/'source.json').read_bytes())
    assert pin(wheels/meta['filename']) == meta['digests']['sha256']
    shutil.copytree(wheels,out/'wheels')
    with zipfile.ZipFile(wheels/meta['filename']) as wheel:
        native, = [n for n in wheel.namelist() if n.endswith('.so')]
        (out/'native').mkdir()
        (out/'native/tokenizers.abi3.so').write_bytes(wheel.read(native))
    numerical = REPO/'engine/tompathy_engine/eval/readers'
    src = 'import hashlib\nimport numpy as np\n\n'
    src += selected_source(numerical/'person_halves.py', {'correlations','ranks','resamples','summary'})
    src += '\n\n'+selected_source(numerical/'week_curve.py', {'nested_indices','rank_arms','posts_needed','fixed_profile','choose_endpoint'})
    (out/'registered.py').write_text(src+'\n',encoding='utf8')
    for name in ('reader.py','tables.py','run.py','made.py','README.md'):
        shutil.copyfile(HERE/name,out/name)
    manifest = {p.relative_to(out).as_posix():pin(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return manifest

if __name__ == '__main__':
    assemble(Path(sys.argv[1]))

