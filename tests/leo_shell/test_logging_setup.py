"""Log redaction keeps provider keys that do not use the sk- prefix."""
import logging

from leo_shell.logging_setup import _redact_text, setup_logging


def test_json_secrets_without_an_sk_prefix_are_redacted():
    text = '{"apiKey": "AIzaSyExample", "token": "plain-token", "password": "p"}'
    redacted = _redact_text(text)
    assert "AIzaSyExample" not in redacted
    assert "plain-token" not in redacted
    assert "p" not in redacted.split("password", 1)[-1]


def test_a_registered_literal_is_removed_from_the_log_line(tmp_path):
    logger = setup_logging(type("Paths", (), {"logs": tmp_path})(), verbose=False)
    from leo_shell.logging_setup import register_redaction
    register_redaction("super-secret-value")
    logger.info("connected with super-secret-value")
    for handler in logger.handlers:
        handler.flush()
    logged = (tmp_path / "leo-shell.log").read_text(encoding="utf-8")
    assert "super-secret-value" not in logged
    assert "<redacted>" in logged
    logging.getLogger("leo_shell").handlers.clear()
