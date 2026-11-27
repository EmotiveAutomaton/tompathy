"""Registered aggregate tables. All indices and author-level intermediates stay in memory."""
import csv
import hashlib
import re
from collections import Counter, defaultdict

import numpy as np
import registered as reg

TAGS = 'contact order status family approval curiosity tranquility competition savings indep food health power romance honor serenity idealism rest belonging'.split()
TRAITS = 'Openness Extraversion Agreeableness Conscientiousness Neuroticism'.split()
NEEDS = ['Competence','Respect','Belonging','Meaning','worry']
GROUPS = [['curiosity'],['status','approval','power','competition','honor'],['family','contact','belonging'],['order','savings','serenity']]
FORMS = re.compile(r"[^\W_]+(?:['’][^\W_]+)*")
ARMS = ['tagsRaw','tagsPartial','placeboRaw','placeboPartial']
SPLITS = ['date','gap']
KS = ['5','10','20','40']

def schema(categories):
    return [list(categories)+['n','value','lo','hi'],[['lo','hi']],categories]

def contracts():
    curves = dict(split=SPLITS,arm=ARMS,k=KS,tag=TAGS+['mean'])
    result = {
        'traits.csv': schema(dict(reading=NEEDS+['family','contact','belonging'],trait=TRAITS)),
        'contrast.csv': schema(dict(stat=['diagonalMinusOther'])),
        'channels.csv': schema(dict(channel=['PLAY','SEEKING'])),
        'stability.csv': schema(curves),
        'fixed_profile.csv': schema(curves),
        'posts_needed.csv': schema(dict(split=SPLITS,arm=ARMS,target=['0.5','0.8'],tag=TAGS)),
        'matching.csv': schema(dict(split=SPLITS,arm=ARMS,k=KS,cut=['1','10'],stat=['baseline','plus','step'])),
        'growth.csv': schema(dict(split=SPLITS,arm=ARMS,k=KS,cut=['1','10'])),
        'curve_check.csv': schema(dict(split=SPLITS,arm=ARMS,k=KS))
    }
    result['contrast.csv'][0].extend(['positiveLeaders','mapPass'])
    return result

class Output:
    def __init__(self):
        self.rows = defaultdict(list)

    def add(self, file, labels, n, estimates):
        if n < 11 or not np.isfinite(estimates[0]):
            return
        draws = estimates[1:][np.isfinite(estimates[1:])]
        if not len(draws):
            return
        interval = np.quantile(draws,[.025,.975])
        self.rows[file].append([*labels,n,*[format(v,'.8g') for v in (estimates[0],*interval)]])

    def write(self, directory):
        directory.mkdir(exist_ok=False)
        for name,rows in self.rows.items():
            with (directory/name).open('x',encoding='utf8',newline='') as stream:
                writer = csv.writer(stream,lineterminator='\n')
                writer.writerow(contracts()[name][0])
                writer.writerows(rows)

def weights(n):
    return np.vstack((np.ones(n),reg.resamples(n)))

def correlations(left,right,w):
    return np.vstack([reg.correlations(left,right,batch) for batch in np.array_split(w,40)])

def trait_tables(scores,traits,output):
    owners = sorted(scores)
    n = len(owners)
    if n < 11:
        return
    readings = np.stack([scores[a] for a in owners])
    target = np.array([traits[a] for a in owners])
    tags = readings[:,:19]
    dev = tags.std(0)
    standardized = np.divide(tags-tags.mean(0),dev,out=np.full_like(tags,np.nan),where=dev>0)
    columns = [standardized[:,[TAGS.index(t) for t in g]].mean(1) for g in GROUPS]
    levels = np.column_stack([*columns,readings[:,38],*[tags[:,TAGS.index(t)] for t in GROUPS[2]]])
    w = weights(n)
    c = correlations(levels.repeat(5,axis=1),np.tile(target,(1,levels.shape[1])),w).reshape(-1,levels.shape[1],5)
    for i,reading in enumerate(NEEDS+GROUPS[2]):
        for j,trait in enumerate(TRAITS):
            output.add('traits.csv',[reading,trait],n,c[:,i,j])
    diagonal = np.eye(5,dtype=bool)
    square = c[:,:5,:]
    output.add('contrast.csv',['diagonalMinusOther'],n,square[:,diagonal].mean(1)-square[:,~diagonal].mean(1))
    matched = square[0].diagonal()
    if np.isfinite(square[0]).all() and output.rows['contrast.csv']:
        is_leader = [(v>0 and v>np.delete(square[0,i,:],i).max() and
                      v>np.delete(square[0,:,i],i).max()) for i,v in enumerate(matched)]
        draws = (square[:,diagonal].mean(1)-square[:,~diagonal].mean(1))[1:]
        lo = np.quantile(draws[np.isfinite(draws)],.025)
        output.rows['contrast.csv'][0].extend([sum(is_leader),int(sum(is_leader)>=4 and lo>0)])
    pair = correlations(readings[:,[40,39]],target[:,[-1,-1]],w)
    for j,channel in enumerate(['PLAY','SEEKING']):
        output.add('channels.csv',[channel],n,pair[:,j])

def style(text, forms, topics):
    words = FORMS.findall(text)
    n = max(1,len(words))
    counts = Counter(w.casefold() for w in words)
    return [len(words),sum(map(len,words))/n,*[100*counts[k]/n for k in forms],
            *[100*text.count(k)/n for k in ',.!?'],100*(text.count("'")+text.count('’'))/n,
            sum(w[0].isupper() for w in words)/n,*[100*counts[k]/n for k in topics]]

def profiles(groups,deep,texts,score,forms):
    outside = set(groups)-deep
    vocabulary = Counter()
    for author in outside:
        for _,_,key in groups[author]:
            vocabulary.update(FORMS.findall(texts[key].casefold()))
    topics = sorted(vocabulary.keys()-set(forms), key=lambda w:(-vocabulary[w],w))[:300]
    # Absent vocabulary dimensions are identically zero; never fit topics on held authors.
    topics += ['']*(300-len(topics))
    if len(deep)<11:
        return {}
    vectors = np.array([style(t,forms,topics) for t in texts])
    joint = np.column_stack((vectors,score[:,:38]))
    observations = {a:np.array([k for _,_,k in rows]) for a,rows in groups.items()}
    totals = sum(joint[ix].sum(0) for ix in observations.values())
    n = sum(map(len,observations.values()))
    ix = np.concatenate([observations[a] for a in deep])
    sd = joint[ix,377:].std(0)
    sd[sd==0] = 1
    def depart(a):
        ix = observations[a]
        z = joint[ix]-(totals-joint[ix].sum(0))/(n-len(ix))
        z[:,377:] /= sd
        return z[:,:358],z[:,358:]
    xx = np.zeros((358,358)); xy = np.zeros((358,38))
    sx = np.zeros(358); sy = np.zeros(38); count = 0
    for a in sorted(outside):
        x,y = depart(a)
        xx += x.T@x; xy += x.T@y; sx += x.sum(0); sy += y.sum(0); count += len(x)
    if count:
        gram = xx-np.outer(sx,sx)/count
        scale = np.sqrt(np.maximum(gram.diagonal()/count,0))
        scale[scale==0] = 1
        coef = np.linalg.solve(gram/np.outer(scale,scale)+np.eye(358),(xy-np.outer(sx,sy)/count)/scale[:,None])
    frames = defaultdict(dict)
    for a in sorted(deep,key=lambda a:hashlib.sha256(('TP39:fold:'+a).encode()).digest()):
        x,y = depart(a)
        cleared = y-((x-sx/count)/scale@coef+sy/count) if count else np.full_like(y,np.nan)
        if not count:
            x = np.full_like(x,np.nan)
        z = np.column_stack((x,y,cleared))
        days,ids,_ = zip(*groups[a])
        for split in SPLITS:
            left,right = reg.nested_indices(days,ids,split=='gap')
            for k in map(int,KS):
                if min(len(left),len(right)) >= k:
                    frames[split,k][a] = (z[left[:k]].mean(0),z[right[:k]].mean(0))
    return frames

def learning_tables(frames,deep,output):
    ordered = sorted(deep,key=lambda a:hashlib.sha256(('TP39:fold:'+a).encode()).digest())
    folds = {a:i%2 for i,a in enumerate(ordered)}
    def views(frame,owners):
        a,b = np.stack([frame[x] for x in owners]).transpose(1,0,2)
        return a,b,np.array([folds[x] for x in owners])
    for split in SPLITS:
        for arm,lo in zip(ARMS,(358,396,377,415)):
            block = slice(lo,lo+19)
            baselines = {}
            for k in map(int,KS):
                frame = frames.get((split,k),{})
                if len(frame)<11:
                    continue
                a,b,fold = views(frame,list(frame))
                if not np.isfinite(a[:,block]).all():
                    continue
                w = weights(len(a))
                c = correlations(a[:,block],b[:,block],w)
                for tag,estimate in zip(TAGS+['mean'],[*c.T,c.mean(1)]):
                    output.add('stability.csv',[split,arm,k,tag],len(a),estimate)
                if k==5:
                    for j,tag in enumerate(TAGS):
                        for target in (.5,.8):
                            estimate = reg.posts_needed(c[:,j],target)
                            output.add('posts_needed.csv',[split,arm,target,tag],len(a),estimate)
                    for k2 in map(int,KS):
                        p = reg.fixed_profile(c,k2)
                        for tag,estimate in zip(TAGS+['mean'],[*p.T,p.mean(1)]):
                            output.add('fixed_profile.csv',[split,arm,k2,tag],len(a),estimate)
                if not np.isfinite(a[:,:358]).all() or min(np.bincount(fold,minlength=2))<2:
                    continue
                base,plus = reg.rank_arms(a,b,[slice(0,358),block],fold,lambda:None)
                baselines[k] = {}
                for cut,endpoint in [(1,'firstOne'),(10,'firstTen')]:
                    raw,added = (base<=cut).astype(float),(plus<=cut).astype(float)
                    baselines[k][endpoint] = raw.mean()
                    for stat,values in [('baseline',raw),('plus',added),('step',added-raw)]:
                        output.add('matching.csv',[split,arm,k,cut,stat],len(a),w@values/len(a))
            if 5 not in baselines:
                continue
            endpoint,kmax = reg.choose_endpoint(baselines,sorted(baselines))
            for k in sorted({max(baselines),kmax or 5}):
                low,high = frames[split,5],frames[split,k]
                owners = [a for a in low if a in high]
                if len(owners)<11:
                    continue
                w = weights(len(owners))
                cs,steps = [],[]
                for f in (low,high):
                    a,b,fold = views(f,owners)
                    cs.append(correlations(a[:,block],b[:,block],w))
                    if k==kmax and min(np.bincount(fold,minlength=2))>=2:
                        r,s = reg.rank_arms(a,b,[slice(0,358),block],fold,lambda:None)
                        cut = 10 if endpoint=='firstTen' else 1
                        steps.append((s<=cut).astype(float)-(r<=cut).astype(float))
                if k==max(baselines):
                    output.add('curve_check.csv',[split,arm,k],len(owners),(cs[1]-reg.fixed_profile(cs[0],k)).mean(1))
                if len(steps)==2:
                    output.add('growth.csv',[split,arm,k,cut],len(owners),w@(steps[1]-steps[0])/len(owners))

