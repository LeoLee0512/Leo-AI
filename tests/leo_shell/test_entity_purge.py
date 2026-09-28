from types import SimpleNamespace
import pytest
from leo_shell.api import ShellApi
from leo_shell.entity_store import EntityStore
from leo_shell.workbench import WorkbenchGateway, route
import io


def setup(tmp_path, fail=False):
    api=ShellApi(None,None,paths=SimpleNamespace(user=tmp_path))
    seen=[]
    class Gateway:
        def purge(self,kind,ident):
            seen.append((kind,ident))
            if fail: raise ValueError('WORKBENCH_UNAVAILABLE')
            return {'ok':True}
    api._workbench_gateway=Gateway()
    return api,seen


@pytest.mark.parametrize('kind',['session','project'])
def test_purge_requires_recycle_revision_and_exact_confirmation(tmp_path,kind):
    api,seen=setup(tmp_path)
    record={'entity_type':kind,'entity_id':'item-1','title':'Test','state':'archived'}
    if kind=='project':record['snapshot']={'snapshot_version':1,'member_session_ids':['f-child']}
    archived=api.mark_entity(record)['entity']
    p={'entity_type':kind,'entity_id':'item-1','expected_revision':archived['revision'],'confirm_id':'item-1'}
    assert not api.purge_entity(p)['ok']
    trashed=api.mark_entity({**record,'state':'trashed'})['entity']
    assert not api.purge_entity(p)['ok']
    p['expected_revision']=trashed['revision']
    assert not api.purge_entity({**p,'confirm_id':'different'})['ok']
    assert not seen
    api.mark_entity({'entity_type':'session','entity_id':'f-unrelated','state':'archived'})
    if kind=='project':api.mark_entity({'entity_type':'session','entity_id':'f-child','state':'trashed'})
    assert api.purge_entity(p)['ok']
    assert seen==[(kind,'item-1')]
    assert [r['entity_id'] for r in api.list_entity_states()['entities']]==['f-unrelated']
    assert not api.purge_entity(p)['ok']


def test_failed_remote_delete_retains_recovery_record(tmp_path):
    api,seen=setup(tmp_path,True)
    r=api.mark_entity({'entity_type':'session','entity_id':'f-1','state':'trashed'})['entity']
    before=(tmp_path/'entity-states.json').read_bytes()
    assert api.purge_entity({'entity_type':'session','entity_id':'f-1','expected_revision':r['revision'],'confirm_id':'f-1'})['message']=='WORKBENCH_UNAVAILABLE'
    assert (tmp_path/'entity-states.json').read_bytes()==before
    assert api.restore_entity({'entity_type':'session','entity_id':'f-1','expected_revision':r['revision']})['ok']


@pytest.mark.parametrize('kind,path',[('session','/frames/id-1'),('project','/projects/id-1')])
def test_native_purge_uses_exact_owned_backend_route(kind,path):
    seen=[]
    class Opener:
        def open(self,request,timeout):
            seen.append(request)
            return io.BytesIO(b'{"ok":true,"deleted":true}')
    gateway=WorkbenchGateway(lambda:'http://127.0.0.1:8760/?token=fixture-token',Opener())
    gateway.purge(kind,'id-1')
    assert seen[0].method=='DELETE'
    assert seen[0].full_url.endswith('/api/v1'+path)
    with pytest.raises(ValueError):gateway.purge(kind,'../other')
    with pytest.raises(ValueError):route({'operation':'purge','frameId':'id-1'})
