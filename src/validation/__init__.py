"""
Validation Framework for SEC Filing Analysis

This module implements the FACT framework and GOALIE protection system
for ensuring accuracy and reliability in financial analysis.
"""

from .fact import FACTValidator
from .goalie import GOALIEProtection
from .metrics import ValidationMetrics

__all__ = ['FACTValidator', 'GOALIEProtection', 'ValidationMetrics']

__version__ = '1.0.0'
