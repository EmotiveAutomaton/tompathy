"""Frozen CPU forward pass for the two distinct MiniLMs and all weekly heads."""
import importlib.util
import json
import math
import os
import struct
import sys
from pathlib import Path

for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '2'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import numpy as np
from scipy.special import erf, expit, softmax

ROOT = Path(__file__).resolve().parent

def tokenizer_class():
    if sys.platform != 'linux':
        from tokenizers import Tokenizer
        return Tokenizer
    library = ROOT/'native/tokenizers.abi3.so'
    spec = importlib.util.spec_from_file_location('tokenizers',library)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Tokenizer

class Encoder:
    def __init__(self, directory):
        cfg = json.loads((directory/'config.json').read_bytes())
        self.heads = cfg['num_attention_heads']
        self.layers = cfg['num_hidden_layers']
        self.eps = cfg['layer_norm_eps']
        if cfg['model_type'] != 'bert' or cfg['hidden_act'] != 'gelu':
            raise ValueError('Unexpected frozen architecture')
        self.tokenizer = tokenizer_class().from_file(str(directory/'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=128)
        self.tokenizer.enable_padding(pad_id=0,pad_token='[PAD]')
        path = directory/'model.safetensors'
        with path.open('rb') as stream:
            size = struct.unpack('<Q',stream.read(8))[0]
            header = json.loads(stream.read(size))
        self.weights = {key:np.memmap(path,mode='r',dtype='<f4',offset=8+size+value['data_offsets'][0],
                                      shape=tuple(value['shape']))
                        for key,value in header.items() if value.get('dtype')=='F32'}

    def encode(self, texts):
        items = self.tokenizer.encode_batch(list(texts))
        ids = np.array([r.ids for r in items])
        mask = np.array([r.attention_mask for r in items],dtype=bool)
        w = self.weights
        def layer_norm(x, key):
            centered = x-x.mean(-1,keepdims=True)
            return centered/np.sqrt(np.mean(centered**2,axis=-1,keepdims=True)+self.eps)*w[key+'.weight']+w[key+'.bias']
        def affine(x,key):
            return x @ w[key+'.weight'].T+w[key+'.bias']
        prefix = 'embeddings.'
        x = w[prefix+'word_embeddings.weight'][ids]+w[prefix+'token_type_embeddings.weight'][0]
        x = layer_norm(x+w[prefix+'position_embeddings.weight'][:ids.shape[1]],prefix+'LayerNorm')
        batch,length,width = x.shape
        for layer in range(self.layers):
            key = f'encoder.layer.{layer}.'
            def attention(name):
                y = affine(x,key+'attention.self.'+name)
                return y.reshape(batch,length,self.heads,-1).transpose(0,2,1,3)
            q,k,v = (attention(name) for name in ('query','key','value'))
            logits = (q @ k.swapaxes(-1,-2))/math.sqrt(width//self.heads)
            probs = softmax(np.where(mask[:,None,None,:],logits,-np.inf),axis=-1)
            mixed = (probs @ v).transpose(0,2,1,3).reshape(batch,length,width)
            x = layer_norm(x+affine(mixed,key+'attention.output.dense'),key+'attention.output.LayerNorm')
            y = affine(x,key+'intermediate.dense')
            y = .5*y*(1+erf(y/math.sqrt(2)))
            x = layer_norm(x+affine(y,key+'output.dense'),key+'output.LayerNorm')
        x = (x*mask[:,:,None]).sum(1)/mask.sum(1,keepdims=True).astype('f4')
        return x/np.linalg.norm(x,axis=1,keepdims=True)

class Readers:
    def __init__(self):
        models = ROOT/'models'
        self.base = Encoder(models/'base')
        self.worry = Encoder(models/'worry')
        def load(file):
            with np.load(models/file,allow_pickle=False) as data:
                return dict(data)
        self.tags = load('tags.npz')
        self.worry_head = load('worry.npz')
        self.channel = load('channels.npz')
        self.pride = load('pride.npz')['theta']
        seed = int.from_bytes(__import__('hashlib').sha256(b'TP45:placebo:23').digest()[:8],'big')
        w = np.random.default_rng(seed).normal(size=self.tags['weights'].shape)
        self.placebo = w/np.linalg.norm(w,axis=1,keepdims=True)

    def score(self,texts):
        base = self.base.encode(texts)
        h = self.channel
        p = h['parameters']
        nine = np.tile(h['constants'],(len(texts),1))
        nine[:,h['active']] = expit(base.astype(float)@p[:-1]+p[-1])
        worry = self.worry.encode(texts)@self.worry_head['weights'].T+self.worry_head['bias']
        return np.column_stack((expit(base@self.tags['weights'].T+self.tags['bias']),
                                base@self.placebo.T,worry,nine,
                                expit(base.astype(float)@self.pride[:-1]+self.pride[-1])))

