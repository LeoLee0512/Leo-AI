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


# --- review fixes: clipboard paste, appearance hand-off, menubar and text zoom ---

import ctypes
import re
from pathlib import Path

from leo_shell import clipboard

STAGE = Path(__file__).resolve().parents[2] / 'stage'


class _FakeClipboard:
    """Just enough of user32/kernel32 for get_text: a buffer and an open counter."""

    def __init__(self, text=None, busy=0):
        # Windows hands out UTF-16-LE; build the bytes explicitly so the fake is portable.
        self.buffer = None if text is None else ctypes.create_string_buffer((text + '\0').encode('utf-16-le'))
        self.busy, self.opens, self.closed, self.unlocked = busy, 0, 0, 0

    def OpenClipboard(self, _):
        self.opens += 1
        return self.opens > self.busy

    def GetClipboardData(self, _):
        return 1 if self.buffer is not None else 0

    def GlobalSize(self, _):
        return ctypes.sizeof(self.buffer)

    def GlobalLock(self, _):
        return ctypes.addressof(self.buffer)

    def GlobalUnlock(self, _):
        self.unlocked += 1

    def CloseClipboard(self):
        self.closed += 1


def test_paste_retries_a_busy_clipboard_then_reads_text(monkeypatch):
    monkeypatch.setattr(clipboard.time, 'sleep', lambda _: None)
    fake = _FakeClipboard('粘贴文本\nsecond line', busy=3)
    assert clipboard.get_text(api=(fake, fake)) == '粘贴文本\nsecond line'
    assert fake.opens == 4 and fake.closed == 1 and fake.unlocked == 1
    assert clipboard.get_text(api=(_FakeClipboard(None), _FakeClipboard(None))) == ''


def test_paste_reports_busy_and_oversized_clipboards_with_known_codes(monkeypatch):
    monkeypatch.setattr(clipboard.time, 'sleep', lambda _: None)
    busy = _FakeClipboard('x', busy=50)
    with pytest.raises(clipboard.ClipboardError, match='CLIPBOARD_BUSY'):
        clipboard.get_text(api=(busy, busy))
    assert busy.closed == 0
    huge = _FakeClipboard('x')
    huge.GlobalSize = lambda _: (clipboard.MAX_CLIPBOARD_CHARS + 2) * 2
    with pytest.raises(clipboard.ClipboardError, match='CLIPBOARD_TEXT_INVALID'):
        clipboard.get_text(api=(huge, huge))
    assert huge.closed == 1
    script = (STAGE / 'workbench.js').read_text(encoding='utf-8')
    for code in ('CLIPBOARD_UNAVAILABLE', 'CLIPBOARD_BUSY', 'CLIPBOARD_TEXT_INVALID'):
        assert re.search(code + r":'[^']+'", script), f'{code} needs user-facing text'


def test_appearance_intent_is_consumed_exactly_once():
    from leo_shell.api import ShellApi
    api = ShellApi(settings=None, coordinator=None)
    assert api.appearance_intent({'operation': 'take'}) == {'ok': True, 'intent': None}
    assert api.appearance_intent({'operation': 'set', 'intent': 'chat'}) == {'ok': True}
    assert api.appearance_intent({'operation': 'take'}) == {'ok': True, 'intent': 'chat'}
    assert api.appearance_intent({'operation': 'take'}) == {'ok': True, 'intent': None}
    for bad in ({'operation': 'set', 'intent': 'javascript:'}, {'operation': 'peek'}, None, 'set'):
        assert api.appearance_intent(bad)['ok'] is False
    assert api.appearance_intent({'operation': 'take'})['intent'] is None
    shell = (STAGE / 'shell.html').read_text(encoding='utf-8')
    workbench = (STAGE / 'workbench.js').read_text(encoding='utf-8')
    assert 'sessionStorage' not in shell and 'sessionStorage' not in workbench
    assert "appearance_intent" in shell and "native('appearance_intent',{operation:'take'})" in workbench


def test_menubar_owns_only_menu_items_and_text_zoom_reaches_the_reading_areas():
    from html.parser import HTMLParser

    class Tree(HTMLParser):
        def __init__(self):
            super().__init__(); self.stack, self.menubar_children, self.depth = [], [], None
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if self.depth is not None and len(self.stack) == self.depth:
                self.menubar_children.append((tag, attrs.get('role')))
            self.stack.append(tag)
            if attrs.get('role') == 'menubar':
                self.depth = len(self.stack)
        def handle_endtag(self, tag):
            if self.stack:
                self.stack.pop()
            if self.depth is not None and len(self.stack) < self.depth:
                self.depth = None

    tree = Tree(); tree.feed((STAGE / 'workbench.html').read_text(encoding='utf-8'))
    assert tree.menubar_children and all(role in ('none', 'menuitem') for _, role in tree.menubar_children), tree.menubar_children
    css = (STAGE / 'workbench.css').read_text(encoding='utf-8')
    assert '--text-scale:1' in css
    for selector in ('.message{', '.composer textarea{', '.leo-research-body>p{'):
        rule = css[css.index(selector):]; rule = rule[:rule.index('}')]
        assert 'var(--text-scale)' in rule, selector
    script = (STAGE / 'workbench.js').read_text(encoding='utf-8')
    assert "setProperty('--text-scale'" in script and 'style.fontSize' not in script
