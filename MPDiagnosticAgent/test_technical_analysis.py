#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test technical analysis feature
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.unified_agent import UnifiedAgent
from core.config import Config

def main():
    print("="*70)
    print("Testing TECHNICAL ANALYSIS")
    print("="*70)
    print()

    # Create agent
    config = Config()
    agent = UnifiedAgent(config=config)

    # Test technical analysis
    print("Testing questions that trigger technical analysis:")
    print()

    questions = [
        "проанализируй логи, какие предложения по настройке можешь дать?",
        "какие настройки двигателей?",
        "проверь вибрации",
        "технический аудит"
    ]

    for q in questions:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print(f"{'='*70}\n")

        answer = agent.answer_question(q)
        print(answer)
        print()

        # Only test first one for now
        break

if __name__ == '__main__':
    main()
