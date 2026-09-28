"""An update-only preview must not blame the model or touch a live daemon."""
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from leo_shell.bridge_client import BridgeError, WslBridge
from leo_shell.connection import ConnectionCoordinator


@pytest.mark.parametrize('mode', ['unconfigured', 'keyless', 'cloud'])
@pytest.mark.parametrize('launcher_is_directory', [False, True])
def test_incomplete_preview_fails_before_wsl_and_keeps_settings_closed(tmp_path, mode, launcher_is_directory):
    script = tmp_path / 'bridge/leo_bridge.sh'
    if launcher_is_directory:
        script.mkdir(parents=True)
    calls = []
    bridge = WslBridge(SimpleNamespace(bridge_script=script), runner=lambda *a, **kw: calls.append(a))
    done = threading.Event()

    class Sink:
        def __init__(self):
            self.statuses = []
            self.settings = 0
            self.navigations = []

        def publish_status(self, message, *, error=False):
            self.statuses.append((message, error))
            done.set()

        def open_settings(self):
            self.settings += 1

        def navigate(self, url):
            self.navigations.append(url)

    sink = Sink()
    coordinator = ConnectionCoordinator(bridge, sink)
    profile = SimpleNamespace(provider='chatgpt', model='model', base_url='', entry_mode=mode)
    try:
        coordinator.submit(profile, 'secret-not-for-ui' if mode == 'cloud' else None, requires_ack=False)
        assert done.wait(5)
    finally:
        coordinator.close(stop_daemon=False)
    assert sink.statuses == [('APP_PACKAGE_INCOMPLETE', True)]
    assert sink.settings == 0
    assert sink.navigations == []
    assert calls == []
    assert coordinator.runtime_state()['status'] == 'failed'


def test_missing_package_error_does_not_expose_path(tmp_path):
    script = tmp_path / 'private-user/bridge/leo_bridge.sh'
    bridge = WslBridge(SimpleNamespace(bridge_script=script), runner=lambda *a, **kw: pytest.fail('spawned WSL'))
    with pytest.raises(BridgeError) as caught:
        bridge.preflight()
    assert caught.value.code == 'APP_PACKAGE_INCOMPLETE'
    assert str(tmp_path) not in str(caught.value)
