# -*- coding: utf-8 -*-
"""
MPDiagnosticAgent Core Module
Unified diagnostic engine for Mission Planner and ArduPilot drones
"""

__version__ = '5.0.0'
__author__ = 'Claude + User'

# Core modules
from .config import Config
from .knowledge_base import KnowledgeBase
from .log_analyzer import LogAnalyzer
from .mavlink_interface import MAVLinkInterface
from .log_downloader import LogDownloader

# Upcoming modules (to be implemented)
# from .diagnostic_engine import DiagnosticEngine

__all__ = [
    'Config',
    'KnowledgeBase',
    'LogAnalyzer',
    'MAVLinkInterface',
    'LogDownloader',
]
