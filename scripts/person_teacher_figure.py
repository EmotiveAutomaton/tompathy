"""Render only public aggregates, alongside the corresponding result sheet."""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def render(source, destination):
    result=json.loads(source.read_bytes())
    card=result['card']
    labels,points,intervals,colors=[],[],[],[]
    def row(name,point,interval=None,color='#28647b'):
        if point is not None:
            labels.append(name)
            points.append(point)
            intervals.append(interval)
            colors.append(color)
    if card=='TP39':
        for k,v in result['estimate']['sets'].items():
            row(k+' · mean',v['value'],v['interval'])
            p=v['inverseVariance']
            if p:
                row(k+' · inverse variance',p['value'],p['interval'],'#8c4b36')
        xlabel='Correlation between a writer’s two halves'
        title='Which sets of readings repeat across halves?'
    elif card=='TP40':
        for k,v in result['estimate']['ratio'].items():
            row(k,v['value'],v['interval'])
        v=result['estimate']['pooledRatio']
        if v:
            row('Pooled across sources',v['value'],v['interval'],'#8c4b36')
        xlabel='Ratio of whole reports with no change, standing words / other words'
        title='Do standing-state words more often describe no change?'
    elif card=='TP34-BK':
        data=result['estimate']
        null=data['words']['all']
        row('All situations',null['share'],null['interval'],'#303030')
        variances=[]; estimates=[]
        for k in data['rank']:
            v=data['words'][k]
            row(k,v['share'],v['interval'])
            variances.append(((v['interval'][1]-v['interval'][0])/3.92)**2)
            estimates.append(v['share'])
        if all(x>0 for x in variances):
            pool=float(np.average(estimates,weights=1/np.asarray(variances)))
            row(f'Word-level precision mean ({pool:.1%})',pool,color='#8c4b36')
        xlabel='Share of situations with every output below or at its quiet threshold'
        title='Which words leave the nine outputs quiet?'
    elif card=='G2-first-rungs':
        for k,v in result['rungs'].items():
            for seed,values in v['comparison']['perSeed'].items():
                row(k.split('/')[-1]+' / '+seed,values['gain'])
        xlabel='Gain over frozen mean AUC'
        title='Did any fitted encoder reach the required gain of .02?'
    elif card=='TP24-chat':
        r=result['row']
        row('Chat, seven eligible groups',r['accuracyOnAllEligible'])
        row('Recalled reports, five groups',r['recalledFiveWordAccuracy'],color='#8c4b36')
        xlabel='Fraction of eligible reports assigned the correct word group'
        title='How often did the table recover the assigned group?'
    elif card=='TP39-change':
        for k,v in result['estimate']['readings'].items():
            row(k,v['value'],v['interval'])
        xlabel='Correlation between a writer’s two halves'
        title='Do change readings repeat within writers?'
    else:
        raise ValueError('Unregistered figure')
    if not labels:
        return
    fig,ax=plt.subplots(figsize=(7.6,max(2.7, .27*len(labels)+1.6)),layout='constrained')
    y=np.arange(len(labels))
    for i,point in enumerate(points):
        if intervals[i]:
            ax.hlines(i,*intervals[i],color=colors[i],linewidth=1.7)
        ax.scatter(point,i,color=colors[i],s=29,zorder=2)
    if card=='G2-first-rungs':
        ax.axvline(.02,color='#666666',ls='--',lw=1)
    if card=='TP40':
        ax.axvline(1,color='#666666',ls=':',lw=1)
        ax.axvline(2,color='#666666',ls='--',lw=1)
    ax.set_yticks(y,labels)
    ax.invert_yaxis()
    ax.spines[['top','right']].set_visible(False)
    ax.set_xlabel(xlabel)
    ax.set_title(title,loc='left',fontsize=12)
    fig.savefig(destination,dpi=145)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    render(args.source,args.output)
