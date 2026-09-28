import json
import sqlite3
import pytest
from leo_shell.local_accounts import LocalAccounts


def test_local_account_roundtrip_recovery_and_restart(tmp_path):
    store = LocalAccounts(tmp_path)
    result = store.request({'operation':'register','email':' User@Example.com ','password':'a-long-password'})
    code = result['recovery_code']
    assert result['account']['email'] == 'user@example.com'
    assert LocalAccounts(tmp_path).request({'operation':'state'})['account'] == result['account']
    raw = store.path.read_bytes()
    assert b'a-long-password' not in raw and code.encode() not in raw
    store.request({'operation':'logout'})
    assert store.request({'operation':'state'})['account'] is None
    assert not store.request({'operation':'login','email':'user@example.com','password':'wrong-password'})['ok']
    assert store.request({'operation':'login','email':'user@example.com','password':'a-long-password'})['ok']
    reset = store.request({'operation':'reset','email':'user@example.com','password':'new-password-long','recovery_code':code})
    assert reset['ok'] and reset['recovery_code'] != code
    assert not store.request({'operation':'reset','email':'user@example.com','password':'other-password','recovery_code':code})['ok']
    assert not store.request({'operation':'login','email':'user@example.com','password':'a-long-password'})['ok']
    assert store.request({'operation':'login','email':'user@example.com','password':'new-password-long'})['ok']


def test_accounts_fail_closed_and_limit_attempts(tmp_path):
    s = LocalAccounts(tmp_path)
    with pytest.raises(ValueError):
        s.request({'operation':'register','email':'no-email','password':'123'})
    s.request({'operation':'register','email':'u@example.com','password':'long-password'})
    with pytest.raises(ValueError,match='ACCOUNT_EXISTS'):
        s.request({'operation':'register','email':'U@example.com','password':'different-password'})
    for _ in range(5):
        assert not s.request({'operation':'login','email':'u@example.com','password':'wrong-password'})['ok']
    assert LocalAccounts(tmp_path).request({'operation':'login','email':'u@example.com','password':'long-password'})['message']=='ACCOUNT_RETRY_LATER'
    assert not s.request({'operation':'login','email':'nobody@example.com','password':'long-password'})['ok']


def test_corrupt_account_database_is_not_replaced(tmp_path):
    p=tmp_path/'local-accounts.sqlite3';p.write_bytes(b'not a sqlite database')
    with pytest.raises(sqlite3.DatabaseError):
        LocalAccounts(tmp_path).request({'operation':'state'})
    assert p.read_bytes()==b'not a sqlite database'
