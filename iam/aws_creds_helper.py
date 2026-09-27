#!/usr/bin/env python3
"""
Backward-compatible entry point.

Use credential_helper.py for new profiles:

    credential_process = /path/to/credential_helper.py profile-oper
"""

from credential_helper import main


if __name__ == "__main__":
    raise SystemExit(main())
