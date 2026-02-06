"""
IO Layer package.

Handles:
- Reading SQL input from files or folders
- Writing validation results to output files
"""

from .reader import read_input
from .writer import write_json_report
