import json
import logging

from business_analyst.observability.logging_config import (
    JsonFormatter,
    log_security_event,
)


def test_json_formatter_outputs_safe_fields():
    logger = logging.getLogger("test.safe.logging")
    record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO,
        fn="test",
        lno=1,
        msg="security_event",
        args=(),
        exc_info=None,
        extra={
            "event": "upload_rejected",
            "status_code": 400,
            "secret_token": "must_not_appear",
        },
    )

    output = JsonFormatter().format(record)
    parsed = json.loads(output)

    assert parsed["event"] == "upload_rejected"
    assert parsed["status_code"] == 400
    assert "secret_token" not in output
    assert "must_not_appear" not in output


def test_security_event_uses_allowlisted_fields(caplog):
    logger = logging.getLogger("test.security.events")

    with caplog.at_level(logging.INFO, logger=logger.name):
        log_security_event(
            logger,
            event="workspace_access_denied",
            status_code=403,
            user_id="user-test-1",
            workspace_id="workspace-test-1",
        )

    assert "security_event" in caplog.text
    assert "workspace_access_denied" in caplog.text
