import numpy as np
import pytest

from tompathy_engine.eval.readers.tp26 import batch_predictions


def test_scalar_batches_survive_interrupt_and_bind_inputs(tmp_path):
    calls=[]
    def predict(texts):
        calls.append(len(texts))
        if len(calls)==2: raise RuntimeError('interrupted')
        return np.full((len(texts),1),4.)
    texts=['text'+str(i) for i in range(33)]
    with pytest.raises(RuntimeError):
        batch_predictions(texts,{'pin':'x'},tmp_path,predict,lambda:None)
    assert len(list(tmp_path.glob('*.json')))==1
    calls.clear()
    def resume(texts):
        calls.append(len(texts));return np.full((len(texts),1),4.)
    out=batch_predictions(texts,{'pin':'x'},tmp_path,resume,lambda:None)
    assert calls==[16,1] and out.shape==(33,1)
    with pytest.raises(ValueError,match='source changed'):
        batch_predictions(texts,{'pin':'changed'},tmp_path,resume,lambda:None)


def test_scalar_denormalization_is_same_linear_head():
    rng=np.random.default_rng(23)
    vectors=rng.normal(size=(16,384)).astype(np.float32)
    vectors/=np.linalg.norm(vectors,axis=1,keepdims=True)
    w=rng.normal(size=(1,384)).astype(np.float32);b=np.array([.2],np.float32)
    mean=np.array([5.],np.float32);scale=np.array([1.8],np.float32)
    np.testing.assert_allclose((vectors@w.T+b)*scale+mean,
        vectors@(w*scale[:,None]).T+b*scale+mean,rtol=1e-6,atol=1e-6)
