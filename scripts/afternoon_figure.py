"""Draw the saved TP41 set estimates and sensitivity to precision weighting."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=Path('engine/validation/readers-tp41-2026-11.json')
e=json.loads(p.read_bytes())['estimate']
fig,ax=plt.subplots(figsize=(7.2,3.5),layout='constrained')
for i,(name,title) in enumerate([('channels','Channels (9)'),('features','Prompted features (8)'),('tags','Need tags (19)')]):
    v=e['sets'][name]['adjusted'];lo,hi=v['interval']
    ax.errorbar(v['value'],i+.10,xerr=[[v['value']-lo],[hi-v['value']]],fmt='o',color='#235b76',capsize=4,
                label='Registered mean and 95% writer interval' if i==0 else None)
    rows=[v['adjusted'] for k,v in e['readings'].items() if k.startswith(name+'/')]
    weights=[1/(v['interval'][1]-v['interval'][0])**2 for v in rows]
    point=sum(v['value']*w for v,w in zip(rows,weights,strict=True))/sum(weights)
    ax.plot(point,i-.12,'D',color='#aa6236',label='Precision-weighted estimate (approx.)' if i==0 else None)
ax.axvline(0,color='#777777',lw=.8)
ax.set_yticks(range(3),['Channels (9)','Prompted features (8)','Need tags (19)'])
ax.set_ylim(-.5,2.5)
ax.set_xlabel('Level-adjusted covariance between writing halves')
ax.set_title('Writers’ responses to pleasant and unpleasant assigned words')
ax.spines[['right','top']].set_visible(False)
fig.legend(loc='outside lower center',frameon=False)
fig.savefig('docs/exchange/result-sheets/TP41.png',dpi=170)
plt.close(fig)
