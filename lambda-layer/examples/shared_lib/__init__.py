"""
Shared library for CLI and Lambda functions.

This module contains the business logic that works from both:
1. Command-line interface (CLI)
2. AWS Lambda handler

The key principle: Pure functions that don't assume the calling environment.
"""

__version__ = "1.0.0"
