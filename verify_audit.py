"""
Check that an audit trail hasn't been altered.
Usage:  python verify_audit.py logs/audit_<session>.jsonl
"""
import sys

from lab_agent.audit import verify

ok, message = verify(sys.argv[1])
print(message)
sys.exit(0 if ok else 1)
