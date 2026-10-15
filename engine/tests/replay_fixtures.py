# Ported from Sounding Line, copyright 2026 Abraham Haskins (MIT).
# See engine/NOTICE-SOUNDING-LINE.txt and reference-sources.json.
from tompathy_engine.adapters.quill import units
from tompathy_engine.adapters.replay import replay
from tompathy_engine.adapters.relations import project

def fixtures():
    cases=[]
    for i in range(16):
        before=f'Workshop {i}: 🌞\n'; offer=f' choice {i}'
        menu=[dict(index=0,original=offer,trimmed=offer)]
        base=[dict(eventName='system-initialize',currentDoc=before),
              dict(eventName='suggestion-open',currentSuggestions=menu)]
        for action in ('accept','edit','dismiss','ignore'):
            rows=list(base)
            end=before
            if action in ('accept','edit'):
                rows += [dict(eventName='suggestion-select',currentSuggestionIndex=0),
                    dict(eventName='text-insert',eventSource='api',textDelta={'ops':[{'retain':len(units(before))-1},{'insert':offer}]})]
                end=before[:-1]+offer+'\n'
                if action=='edit':
                    rows += [dict(eventName='text-insert',eventSource='user',textDelta={'ops':[{'retain':len(units(before))},{'delete':1},{'insert':'X'}]})]
                    end=before[:-1]+' X'+offer[2:]+'\n'
            else:
                if action=='dismiss': rows += [dict(eventName='suggestion-close')]
                rows += [dict(eventName='text-insert',eventSource='user',textDelta={'ops':[{'retain':len(units(before))}]})]
            r=replay(rows); e=r['events'][0]
            assert r['reconstructed'] and e['usable'] and e['decision']==action
            assert e['end_document']==end
            target=project(e,rows)
            assert target['handling']==action
            assert target['attributes']==dict(reviewed='unknown',endorsed='unknown',understood='unknown')
            cases.append(dict(key=f'fixture-{i}-{action}',lines=rows,event=e,target=target))
    bad=list(cases[0]['lines'])+[dict(eventName='text-delete',eventSource='user',textDelta={'ops':[{'delete':1000000}]})]
    assert not replay(bad)['reconstructed']
    return cases
