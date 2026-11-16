"""TP10's preplanned three-seed MiniLM fine-tuning stage, isolated from L0–L2."""
import json
import time
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file, save_file
from sentence_transformers import SentenceTransformer
from sklearn.metrics import f1_score

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .encoders import load_encoder
from .envent import RATINGS, READABLE, load
from .metrics import channel_gates, classification, confusion
from .tp10 import neutral_texts

SEEDS = (23, 47, 71)
EPOCHS = 3
BATCH = 16
CAP = 128


class Heads(torch.nn.Module):
    def __init__(self, encoder, labels):
        super().__init__()
        self.encoder = encoder
        dimension = encoder.get_sentence_embedding_dimension()
        self.labels = torch.nn.Linear(dimension, labels)
        self.ratings = torch.nn.Linear(dimension, 21)

    def forward(self, texts):
        inputs = self.encoder.tokenize(texts)
        vector = self.encoder(inputs)['sentence_embedding']
        vector = torch.nn.functional.normalize(vector, p=2, dim=1)
        return self.labels(vector), self.ratings(vector)


def predict(model, texts, check):
    model.eval()
    probabilities, ratings = [], []
    with torch.inference_mode():
        for start in range(0, len(texts), BATCH):
            check()
            label, features = model(texts[start:start+BATCH])
            probabilities.append(label.softmax(dim=1).numpy())
            ratings.append(features.numpy())
    return np.concatenate(probabilities), np.concatenate(ratings)


def run(directory, models, prepared, ladder, output, check):
    """Only development F1 selects epochs and the export seed; test never tunes."""
    output, ladder, models = Path(output), Path(ladder), Path(models)
    previous = json.loads((ladder/'receipt.json').read_text(encoding='utf8'))
    verified = json.loads((ladder/'exit-verification.json').read_text(encoding='utf8'))
    if not all(verified.get(k) for k in ('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent')):
        raise ValueError('Prior scorer must exit and release')
    if previous['selected_for_L3'] != 'minilm':
        raise ValueError('This registered continuation requires the development-selected MiniLM')
    corpus = load(directory)
    if previous['scope'] != corpus.summary():
        raise ValueError('L3 must retain L0–L2 split and corpus')
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    # Verify original file pins without letting any missing weight download.
    verified_encoder, encoder_identity = load_encoder(models/'minilm', 'minilm', cap=CAP)
    del verified_encoder
    themes, revisions, neutral_intake = neutral_texts(prepared)
    frame, train, dev, test = corpus.reports, corpus.train, corpus.dev, corpus.test
    texts = frame.hidden_emo_text.tolist()
    y, targets = frame.y.to_numpy(), frame[RATINGS].to_numpy(np.float32)
    report = {'card':'TP10-L3', 'status':'running', 'scope':corpus.summary(),
        'ladderReceiptPin':sha256(ladder/'receipt.json'), 'encoder':encoder_identity,
        'hyperparameters':{'seeds':list(SEEDS),'epochs':EPOCHS,'batch':BATCH,'token_cap':CAP,
            'encoder_lr':2e-5,'head_lr':1e-3,'weight_decay':.01,'clip_norm':1.,
            'loss':'label cross-entropy + 0.1 * all-21 rating MSE',
            'initialization':'L2 logistic and ridge heads; original pretrained encoder',
            'selection':'Highest development macro-F1 epoch per seed, then highest development seed; earlier wins ties'},
        'rows':{},'productionAdmission':False,'pack':'pending final gates and TP12 policy'}
    save_json(output/'receipt.json', report)
    readable = [RATINGS.index(r) for r in READABLE]
    for seed in SEEDS:
        check()
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        seed_dir = output/f'seed-{seed}'
        seed_dir.mkdir()
        encoder = SentenceTransformer(str(models/'minilm'), device='cpu', local_files_only=True,
                                      trust_remote_code=False)
        encoder.max_seq_length = CAP
        model = Heads(encoder, len(corpus.labels))
        with np.load(ladder/'minilm-head.npz', allow_pickle=False) as head, torch.no_grad():
            model.labels.weight.copy_(torch.as_tensor(head['weights']))
            model.labels.bias.copy_(torch.as_tensor(head['bias']))
            model.ratings.weight.copy_(torch.as_tensor(head['ratings_weights']))
            model.ratings.bias.copy_(torch.as_tensor(head['ratings_bias']))
        optimizer = torch.optim.AdamW([
            {'params':model.encoder.parameters(),'lr':2e-5},
            {'params':list(model.labels.parameters())+list(model.ratings.parameters()),'lr':1e-3}], weight_decay=.01)
        best, epochs = -1., []
        started = time.perf_counter()
        for epoch in range(EPOCHS):
            model.train()
            order = rng.permutation(train)
            loss_sum = 0.
            for start in range(0,len(order),BATCH):
                check()
                batch = order[start:start+BATCH]
                optimizer.zero_grad(set_to_none=True)
                logits, features = model([texts[i] for i in batch])
                loss = (torch.nn.functional.cross_entropy(logits, torch.as_tensor(y[batch],dtype=torch.long))
                        + .1*torch.nn.functional.mse_loss(features,torch.from_numpy(targets[batch])))
                if not torch.isfinite(loss):
                    raise ValueError('Nonfinite training loss')
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
                optimizer.step()
                loss_sum += float(loss.detach())*len(batch)
                save_json(output/'progress.json',{'seed':seed,'epoch':epoch+1,'examples':min(start+BATCH,len(order)),
                    'total':len(order),'elapsed_seconds':time.perf_counter()-started})
            probabilities, _ = predict(model,[texts[i] for i in dev],check)
            score = float(f1_score(y[dev],probabilities.argmax(axis=1),average='macro'))
            epochs.append({'epoch':epoch+1,'development_macro_f1':score,'mean_loss':loss_sum/len(train)})
            if score > best:
                best = score
                save_file({n:t.detach().cpu().contiguous() for n,t in model.state_dict().items()}, str(seed_dir/'best.safetensors'))
            save_json(seed_dir/'epochs.json',epochs)
        model.load_state_dict(load_file(str(seed_dir/'best.safetensors')))
        p, rated = predict(model,[texts[i] for i in test],check)
        dev_p, _ = predict(model,[texts[i] for i in dev],check)
        theme_p, _ = predict(model,themes,check)
        revision_p, _ = predict(model,revisions,check)
        row = classification(y[test],p,frame.iloc[test].prolific_id,corpus.labels)
        row.update(seed=seed,development_macro_f1=best,epochs=epochs,
                   development_error_counts=confusion(y[dev],dev_p.argmax(axis=1),len(corpus.labels)).tolist())
        rmse = lambda a,b:float(np.sqrt(np.mean((a-b)**2)))
        row['features']={'all21_rmse':rmse(rated,targets[test]),
            'readable8_rmse':rmse(rated[:,readable],targets[test][:,readable]),
            'floor':previous['rows']['minilm']['features']['floor'],'readable':READABLE}
        row['features']['passed']=all(row['features']['readable8_rmse']<v for v in row['features']['floor'].values())
        neutral=corpus.labels.index('no-emotion')
        row['nothing_here']={'theme_free_n':len(themes),'theme_free_silent':int((theme_p.argmax(axis=1)==neutral).sum()),
            'revision_n':len(revisions),'revision_silent_rate':float((revision_p.argmax(axis=1)==neutral).mean()),
            'revision_coverage_complete':neutral_intake.get('coverageComplete',False),
            'revision_exclusions':neutral_intake.get('excluded',{})}
        row['gates']=channel_gates(row,previous['rows']['bow'],row['nothing_here'])
        timing_texts=texts[:150]
        model.eval()
        start=time.perf_counter()
        with torch.inference_mode():
            for i in range(0,150,BATCH):
                model(timing_texts[i:i+BATCH])
        elapsed=time.perf_counter()-start
        row['timing']={'seconds150':elapsed,'sentences_per_second':150/elapsed,'threads':2,
                       'excludes_loading':True,'live_speed_target_met':elapsed<1}
        np.savez(seed_dir/'predictions.npz',test_probabilities=p,development_probabilities=dev_p,
                 theme_probabilities=theme_p,revision_probabilities=revision_p,y=y[test],
                 ratings=rated,writers=frame.iloc[test].prolific_id.to_numpy(str))
        model.encoder.save(str(seed_dir/'encoder'),safe_serialization=True,create_model_card=False)
        np.savez(seed_dir/'head.npz',weights=model.labels.weight.detach().numpy(),bias=model.labels.bias.detach().numpy(),
                 ratings_weights=model.ratings.weight.detach().numpy(),ratings_bias=model.ratings.bias.detach().numpy())
        row['files']={p.relative_to(seed_dir).as_posix():sha256(p) for p in seed_dir.rglob('*') if p.is_file()}
        report['rows'][str(seed)]=row
        save_json(output/'receipt.json',report)
        del model,encoder,optimizer
    selected=max(SEEDS,key=lambda seed:report['rows'][str(seed)]['development_macro_f1'])
    report.update(status='complete',selected_seed=selected,
        mean_accuracy=float(np.mean([r['accuracy'] for r in report['rows'].values()])),
        mean_macro_f1=float(np.mean([r['macro_f1'] for r in report['rows'].values()])))
    report['pack']='eligible for policy/pin checks' if report['rows'][str(selected)]['gates']['pack_eligible'] else 'not qualified; no pack written'
    save_json(output/'receipt.json',report)
    return report
