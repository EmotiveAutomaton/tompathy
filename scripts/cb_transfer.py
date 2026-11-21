"""CB-only configuration of the same pinned, capped, self-transmitting Spark verifier."""
import subprocess
import sys
from pathlib import Path

from afternoon_collect import TRANSFER
from afternoon_report import pin, put

ROOT = Path('.local/person-teacher')
COMMIT = '71e719cc6b7063d2f2516040cf8fde3d2863453a'


def fetch(job):
    if job not in ('Q18','Q19'):
        raise ValueError('Outside CB transfer scope')
    source = Path(__file__).with_name('person_teacher_transfer.py')
    if pin(source) != TRANSFER:
        raise ValueError('Capped verifier changed')
    guard = b"if __name__=='__main__':"
    header, entry = source.read_bytes().split(guard)
    cfg = f"COMMIT={COMMIT!r}\nROOTS={{j:'person-teacher-20261121' for j in ('Q18','Q19')}}\n"
    target = ROOT/'cb/transfer.py'
    put(target, header+cfg.encode()+guard+entry)
    subprocess.run([sys.executable, str(target), job], check=True)


if __name__ == '__main__':
    fetch(sys.argv[1])
