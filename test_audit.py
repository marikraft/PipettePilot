import json

from lab_agent.audit import AuditLog, verify


def test_untouched_log_verifies(tmp_path):
    log = AuditLog(directory=tmp_path)
    log.record("instruction", text="Transfer 50 uL from source A1 to target B1")
    log.record("approval", approved=True)
    assert verify(log.path)[0]


def test_edited_record_is_detected(tmp_path):
    log = AuditLog(directory=tmp_path)
    log.record("approval", approved=False)
    log.record("session_end")
    lines = log.path.read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    entry["data"]["approved"] = True  # someone rewrites history
    lines[0] = json.dumps(entry)
    log.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert not verify(log.path)[0]


def test_deleted_record_is_detected(tmp_path):
    log = AuditLog(directory=tmp_path)
    for event in ["instruction", "validation", "approval"]:
        log.record(event)
    lines = log.path.read_text(encoding="utf-8").splitlines()
    log.path.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")
    assert not verify(log.path)[0]
