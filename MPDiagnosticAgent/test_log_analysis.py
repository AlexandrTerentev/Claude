#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to verify log analysis works
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.unified_agent import UnifiedAgent
from core.config import Config

def main():
    print("="*70)
    print("Testing Downloaded Log Analysis")
    print("="*70)
    print()

    # Create agent
    config = Config()
    agent = UnifiedAgent(config=config)

    # Run analysis
    print("Running analysis...")
    print()
    report = agent.analyze_current_state()

    print()
    print("="*70)
    print("RESULTS")
    print("="*70)
    print()

    print(f"📊 Found {len(report['prearm_errors'])} PreArm errors")
    print(f"🔧 Found {len(report['fixable_issues'])} fixable issues")
    print()

    if agent.downloaded_logs:
        print(f"📁 Analyzed logs:")
        for log in agent.downloaded_logs[:5]:
            size_kb = log.stat().st_size / 1024
            print(f"   • {log.name} ({size_kb:.1f} KB)")
        print()

    if report['prearm_errors']:
        print("❌ PreArm Errors found:")
        for i, error in enumerate(report['prearm_errors'][:10], 1):
            print(f"\n{i}. {error['error']}")
            if 'source' in error:
                print(f"   Source: {error['source']}")
            print(f"   Type: {error['type']}")
            print(f"   Severity: {error['severity']}")
    else:
        print("✅ No PreArm errors found!")

    print()
    print("="*70)
    print("Testing Q&A with downloaded logs")
    print("="*70)
    print()

    question = "посмотри скачанные логи и проанализируй их"
    print(f"Q: {question}")
    print()
    answer = agent.answer_question(question)
    print(f"A:\n{answer}")

if __name__ == '__main__':
    main()
