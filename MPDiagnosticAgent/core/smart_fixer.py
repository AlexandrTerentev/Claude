#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Auto-Fix Generator
Uses Claude AI to generate parameter fixes on-the-fly
"""

import subprocess
import json
import re
from typing import List, Dict, Any

# Import FixAction from unified_agent
try:
    from .unified_agent import FixAction
except ImportError:
    # Fallback definition
    class FixAction:
        def __init__(self, title: str, description: str, params: Dict[str, Any], severity: str = "medium"):
            self.title = title
            self.description = description
            self.params = params
            self.severity = severity
            self.applied = False


class SmartFixer:
    """
    AI-powered fix generator
    Asks Claude to generate parameter fixes based on errors
    """

    def __init__(self):
        """Initialize smart fixer"""
        self.claude_available = self._check_claude_cli()

    def _check_claude_cli(self) -> bool:
        """Check if Claude CLI is available"""
        try:
            result = subprocess.run(
                ["which", "claude"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    def generate_fixes(self, error: str, context: Dict[str, Any] = None) -> List[FixAction]:
        """
        Ask Claude to generate fixes for an error

        Args:
            error: Error message
            context: Additional context (current params, drone state, etc.)

        Returns:
            List of FixAction objects
        """
        if not self.claude_available:
            return self._fallback_fixes(error)

        try:
            # Build prompt for Claude
            prompt = self._build_fix_prompt(error, context)

            # Ask Claude
            result = subprocess.run(
                ["claude", prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0 or not result.stdout:
                return self._fallback_fixes(error)

            # Parse Claude's response
            fixes = self._parse_claude_fixes(result.stdout, error)
            return fixes if fixes else self._fallback_fixes(error)

        except subprocess.TimeoutExpired:
            print("⚠️ Claude timeout - using fallback fixes")
            return self._fallback_fixes(error)
        except Exception as e:
            print(f"⚠️ Error generating smart fixes: {e}")
            return self._fallback_fixes(error)

    def _build_fix_prompt(self, error: str, context: Dict[str, Any] = None) -> str:
        """Build prompt for Claude"""
        prompt = f"""Ты эксперт по ArduPilot. Пользователь получил ошибку PreArm:

ОШИБКА: {error}

ЗАДАЧА: Предложи 2-3 способа исправить эту ошибку через параметры MAVLink.

ФОРМАТ ОТВЕТА - ТОЛЬКО JSON (без лишнего текста!):
[
    {{
        "title": "Краткое название (макс 50 символов)",
        "description": "Что делает это исправление (1-2 предложения)",
        "params": {{
            "PARAM_NAME1": value1,
            "PARAM_NAME2": value2
        }},
        "severity": "low|medium|high|critical"
    }},
    ...
]

ВАЖНО:
1. Используй РЕАЛЬНЫЕ параметры ArduPilot (RC_PROTOCOLS, BATT_MONITOR, GPS_TYPE и т.д.)
2. Указывай ПРАВИЛЬНЫЕ значения (например RC_PROTOCOLS=1 для всех протоколов)
3. Severity: low=косметика, medium=важно, high=критично для взлёта, critical=опасно
4. Вернисамую  ТОЛЬКО JSON массив, БЕЗ markdown, БЕЗ комментариев!

"""

        if context:
            prompt += f"\nДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ:\n{json.dumps(context, indent=2)}\n"

        return prompt

    def _parse_claude_fixes(self, response: str, error: str) -> List[FixAction]:
        """Parse Claude's JSON response into FixAction objects"""
        try:
            # Extract JSON from response (Claude might add extra text)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if not json_match:
                print("⚠️ No JSON found in Claude response")
                return []

            json_str = json_match.group(0)
            fixes_data = json.loads(json_str)

            fixes = []
            for fix_data in fixes_data:
                try:
                    fix = FixAction(
                        title=fix_data.get('title', 'Fix'),
                        description=fix_data.get('description', ''),
                        params=fix_data.get('params', {}),
                        severity=fix_data.get('severity', 'medium')
                    )
                    fixes.append(fix)
                except Exception as e:
                    print(f"⚠️ Error parsing fix: {e}")
                    continue

            return fixes

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            print(f"Response was: {response[:200]}")
            return []
        except Exception as e:
            print(f"⚠️ Error parsing Claude response: {e}")
            return []

    def _fallback_fixes(self, error: str) -> List[FixAction]:
        """Generate basic fixes when Claude is not available"""
        error_lower = error.lower()

        if 'rc not found' in error_lower or 'radio' in error_lower:
            return [
                FixAction(
                    title="Enable All RC Protocols",
                    description="Allow all RC protocols (PPM, SBUS, DSM, etc.)",
                    params={'RC_PROTOCOLS': 1},
                    severity="high"
                )
            ]

        elif 'battery' in error_lower:
            return [
                FixAction(
                    title="Configure Battery Monitor",
                    description="Enable analog voltage+current monitoring",
                    params={'BATT_MONITOR': 4, 'BATT_CAPACITY': 5200},
                    severity="high"
                )
            ]

        elif 'gps' in error_lower:
            return [
                FixAction(
                    title="Enable GPS Auto-detect",
                    description="Set GPS to auto-detect mode",
                    params={'GPS_TYPE': 1},
                    severity="medium"
                )
            ]

        else:
            return []


# Testing
if __name__ == '__main__':
    print("Testing SmartFixer...")
    print("=" * 60)

    fixer = SmartFixer()
    print(f"Claude available: {fixer.claude_available}\n")

    # Test different errors
    test_errors = [
        "PreArm: RC not found",
        "PreArm: Battery 1 below minimum arming voltage",
        "PreArm: GPS not found"
    ]

    for error in test_errors:
        print(f"\n{'='*60}")
        print(f"ERROR: {error}")
        print(f"{'='*60}")

        fixes = fixer.generate_fixes(error)

        if fixes:
            print(f"\nGenerated {len(fixes)} fixes:")
            for i, fix in enumerate(fixes, 1):
                print(f"\n{i}. {fix.title} [{fix.severity}]")
                print(f"   {fix.description}")
                print(f"   Parameters: {fix.params}")
        else:
            print("No fixes generated")

    print("\n" + "=" * 60)
    print("✓ Tests complete")
