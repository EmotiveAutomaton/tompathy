"""Explicit weight acquisition; inference never invokes this module."""
import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from ...packs.registry import sha256

MODELS = {
    'potion': ('minishlab/potion-base-8M', 'mit'),
    'minilm': ('sentence-transformers/all-MiniLM-L6-v2', 'apache-2.0'),
    'smol135': ('HuggingFaceTB/SmolLM2-135M', 'apache-2.0'),
    'achievement': ('theharmonylab/implicit-motives-achievement-roberta-large', None),
    'affiliation': ('theharmonylab/implicit-motives-affiliation-roberta-large', None),
    'power': ('theharmonylab/implicit-motives-power-roberta-large', None),
    'motive-setfit': ('automatedMotiveCoder/setfit', None),
}


def acquire(name, directory):
    from huggingface_hub import HfApi, snapshot_download
    root = Path(directory).resolve()
    if not root.is_relative_to(Path('.local').resolve()):
        raise ValueError('Weights must remain in private local storage')
    if root.exists():
        raise ValueError('Use a fresh weight directory; preserve previous pins')
    repo, expected_license = MODELS[name]
    info = HfApi().model_info(repo, token=False)
    license = (info.card_data or {}).get('license')
    if expected_license and license != expected_license:
        raise ValueError(f'License changed: expected {expected_license}, received {license}')
    # Exclude alternate framework copies and executable remote custom modules.
    snapshot_download(repo, revision=info.sha, local_dir=root, token=False,
        allow_patterns=['config.json', 'model.safetensors', 'tokenizer.json', 'tokenizer_config.json',
                        'special_tokens_map.json', 'vocab.json', 'vocab.txt', 'merges.txt',
                        'sentencepiece.bpe.model', 'config_sentence_transformers.json', 'config_setfit.json',
                        'modules.json', 'sentence_bert_config.json', 'model_head.pkl', 'README.md', 'LICENSE*',
                        '1_Pooling/config.json', '2_Normalize/config.json'],
        ignore_patterns=['onnx/*', 'openvino/*', '*.bin', '*.h5', '*.msgpack'])
    files = {p.relative_to(root).as_posix(): sha256(p) for p in root.rglob('*')
             if p.is_file() and '.cache' not in p.parts}
    receipt = {'source': f'https://huggingface.co/{repo}', 'id': repo, 'revision': info.sha,
        'license_as_read': license, 'research_only': license not in {'mit', 'apache-2.0'},
        'files': files, 'at': datetime.now(UTC).isoformat()}
    (root/'intake.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
    return {k: v for k, v in receipt.items() if k != 'files'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', choices=MODELS)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(acquire(args.name, args.directory)))


if __name__ == '__main__':
    main()
