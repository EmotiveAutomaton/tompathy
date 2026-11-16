"""Convert the pinned SetFit numeric head without importing its pickled classes.

Only inert estimator state and bounded numeric arrays are decoded. Runtime uses
the resulting NPZ; neither joblib.load nor general pickle.load is permitted.
"""
import json
import math
import pickle
from pathlib import Path

import numpy as np
from joblib.numpy_pickle import NumpyArrayWrapper, NumpyUnpickler

from ...packs.registry import sha256


class State:
    def __init__(self, *args, **kwargs):
        pass

    def __setstate__(self, values):
        if not isinstance(values, dict) or any(str(k).startswith('__') for k in values):
            raise ValueError('Only ordinary inert estimator state is accepted')
        self.__dict__.update(values)


class ArrayMarker:
    pass


class NumericArray(NumpyArrayWrapper):
    def read(self, unpickler, ensure_native_byte_order):
        if (self.subclass is not ArrayMarker or self.dtype.hasobject or self.dtype.kind not in 'biuf'
                or not isinstance(self.shape, tuple) or len(self.shape)>2
                or any(type(n) is not int or n<0 or n>100_000 for n in self.shape)
                or math.prod(self.shape)*self.dtype.itemsize>1_000_000
                or self.order not in ('C','F')):
            raise ValueError('Unbounded or nonnumeric pickle array rejected')
        alignment=self.safe_get_numpy_array_alignment_bytes()
        if alignment not in (None,16):
            raise ValueError('Unexpected array alignment')
        return self.read_array(unpickler,ensure_native_byte_order)


class NumericHeadUnpickler(NumpyUnpickler):
    dispatch=NumpyUnpickler.dispatch.copy()

    def find_class(self, module, name):
        if (module,name) in {
            ('sklearn.multiclass','OneVsRestClassifier'),
            ('sklearn.linear_model._stochastic_gradient','SGDClassifier'),
            ('sklearn.preprocessing._label','LabelBinarizer'),
            ('sklearn.linear_model._sgd_fast','Log'),
            ('_loss','CyHalfBinomialLoss'),
        }:
            return State
        if (module,name)==('joblib.numpy_pickle','NumpyArrayWrapper'):
            return NumericArray
        if (module,name)==('numpy','ndarray'):
            return ArrayMarker
        if (module,name)==('numpy','dtype'):
            return np.dtype
        raise ValueError(f'Unapproved pickle global: {module}.{name}')

    def reject_extension(self):
        raise ValueError('Pickle extension registry is forbidden')

    dispatch[pickle.EXT1[0]]=reject_extension
    dispatch[pickle.EXT2[0]]=reject_extension
    dispatch[pickle.EXT4[0]]=reject_extension


def convert(root, output):
    root,output=Path(root),Path(output)
    intake=json.loads((root/'intake.json').read_text(encoding='utf8'))
    path=root/'model_head.pkl'
    if path.stat().st_size>1_000_000 or sha256(path)!=intake['files']['model_head.pkl']:
        raise ValueError('Head size or intake pin differs')
    with path.open('rb') as stream:
        head=NumericHeadUnpickler(str(path),stream,ensure_native_byte_order=True).load()
        if stream.read(1):
            raise ValueError('Trailing pickle payload')
    config=json.loads((root/'config_setfit.json').read_text(encoding='utf8'))
    if config['labels']!=['ach','aff','pow','null'] or head.label_binarizer_.y_type_!='multilabel-indicator':
        raise ValueError('Unexpected motive classes or probability semantics')
    if len(head.estimators_)!=4 or not np.array_equal(head.classes_,np.arange(4)):
        raise ValueError('Unexpected head class order')
    weights,bias=[],[]
    for estimator in head.estimators_:
        if (estimator.loss!='log_loss' or not np.array_equal(estimator.classes_,[0,1])
                or estimator.coef_.shape!=(1,1024) or estimator.intercept_.shape!=(1,)):
            raise ValueError('Unexpected binary logistic head')
        weights.append(estimator.coef_[0])
        bias.append(estimator.intercept_[0])
    weights,bias=np.asarray(weights),np.asarray(bias)
    if not np.isfinite(weights).all() or not np.isfinite(bias).all():
        raise ValueError('Nonfinite head')
    output.mkdir(parents=True,exist_ok=False)
    np.savez(output/'head.npz',weights=weights,bias=bias)
    record={'sourceHeadPin':sha256(path),'sourceIntakePin':sha256(root/'intake.json'),
            'headPin':sha256(output/'head.npz'),'labels':config['labels'],
            'probabilities':'Independent sigmoid outputs; never normalized across motives',
            'converterPin':sha256(Path(__file__)), 'decoder':'Inert estimator states and bounded numeric arrays only'}
    (output/'conversion.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    return record
