import sqlite3
import pytest
from leo_shell.local_accounts import LocalAccounts
from leo_shell.workspace_preferences import WorkspacePreferences

THEME={'name':'Paper','colors':{'paper':'#ffffff','surface':'#fafafa','ink':'#222222','accent':'#345678','rail':'#222222','rail_ink':'#eeeeee'}}
PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZfoAAAAASUVORK5CYII='

def test_profile_requires_login_and_is_scoped_to_current_account(tmp_path):
    s=LocalAccounts(tmp_path)
    with pytest.raises(ValueError,match='ACCOUNT_LOGIN_REQUIRED'):
        s.request({'operation':'update_profile','display_name':'A'})
    s.request({'operation':'register','email':'a@example.com','password':'long-password'})
    result=s.request({'operation':'update_profile','email':'b@example.com','display_name':'Alice','bio':'Notes\nResearch','avatar':PNG})
    assert result['account']['email']=='a@example.com'
    assert result['account']['avatar']==PNG
    assert LocalAccounts(tmp_path).request({'operation':'state'})==result
    s.request({'operation':'register','email':'b@example.com','password':'long-password'})
    assert s.request({'operation':'state'})['account']['display_name']=='b'
    result=s.request({'operation':'login','email':'a@example.com','password':'long-password'})
    assert result['account']['display_name']=='Alice'
    assert result['account']['bio']=='Notes\nResearch'
    assert not {'password','salt','recovery'} & result['account'].keys()
    s.request({'operation':'update_profile','display_name':'Alice','bio':'','avatar':''})
    assert not s.request({'operation':'state'})['account']['avatar']

@pytest.mark.parametrize('extra',[{'display_name':''},{'display_name':'x'*61},{'display_name':'x\0'},{'bio':'x'*501},{'avatar':'javascript:alert(1)'},{'avatar':'data:image/svg+xml,<svg/>'},{'avatar':'data:image/png;base64,YWJj'}])
def test_invalid_profile_does_not_replace_saved_profile(tmp_path,extra):
    s=LocalAccounts(tmp_path);s.request({'operation':'register','email':'a@example.com','password':'long-password'})
    before=s.request({'operation':'state'})
    with pytest.raises(ValueError):s.request({'operation':'update_profile','display_name':'Valid','bio':'','avatar':'',**extra})
    assert s.request({'operation':'state'})==before

def test_legacy_account_database_migrates_without_changing_credentials(tmp_path):
    s=LocalAccounts(tmp_path);s.request({'operation':'register','email':'a@example.com','password':'long-password'})
    with sqlite3.connect(s.path) as db:
        old=db.execute('SELECT * FROM accounts').fetchall();db.execute('DROP TABLE profiles')
    assert LocalAccounts(tmp_path).request({'operation':'state'})['account']['display_name']=='a'
    with sqlite3.connect(s.path) as db:assert db.execute('SELECT * FROM accounts').fetchall()==old

def test_theme_preview_never_persists_and_save_survives_restart(tmp_path):
    s=WorkspacePreferences(tmp_path)
    r=s.request({'operation':'validate','theme':THEME});assert not s.path.exists()
    saved=s.request({'operation':'save','mode':'dark','theme':r['theme']})
    assert WorkspacePreferences(tmp_path).request({'operation':'get'})==saved
    s.request({'operation':'save','mode':'system','theme':None})
    assert s.request({'operation':'get'})['preferences']=={'mode':'system','theme':None}

@pytest.mark.parametrize('value',[{'name':'Bad','colors':{**THEME['colors'],'ink':'#FFFFFF'}},{'name':'Bad','colors':{**THEME['colors'],'accent':'url(https://example.com)'}},{**THEME,'css':'body{}'},None])
def test_theme_rejects_executable_content_and_unreadable_colors(tmp_path,value):
    s=WorkspacePreferences(tmp_path);s.request({'operation':'save','mode':'light','theme':THEME});old=s.path.read_bytes()
    with pytest.raises(ValueError):s.request({'operation':'save','mode':'light','theme':value}) if value is not None else s.request({'operation':'validate','theme':value})
    assert s.path.read_bytes()==old

def test_invalid_preferences_file_is_preserved(tmp_path):
    s=WorkspacePreferences(tmp_path);s.path.write_text('not json')
    with pytest.raises(ValueError):s.request({'operation':'get'})
    assert s.path.read_text()=='not json'
