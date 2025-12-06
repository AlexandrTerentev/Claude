# -*- coding: utf-8 -*-
"""
Knowledge Base Manager for MPDiagnosticAgent
Loads and queries diagnostic rules from JSON files
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class KnowledgeBase:
    """
    Knowledge Base manager for diagnostic rules

    Loads diagnostic knowledge from JSON files and provides
    query interface for retrieving solutions based on keywords
    """

    def __init__(self, knowledge_dir: Optional[Path] = None):
        """
        Initialize Knowledge Base

        Args:
            knowledge_dir: Path to knowledge directory. If None, uses default
        """
        if knowledge_dir is None:
            # Default: knowledge/ directory in project root
            project_root = Path(__file__).parent.parent
            self.knowledge_dir = project_root / 'knowledge'
        else:
            self.knowledge_dir = Path(knowledge_dir)

        # Storage for loaded knowledge
        self.motor_issues = {}
        self.calibration_guides = {}
        self.parameters = {}

        # Load all knowledge files
        self._load_knowledge()

    def _load_knowledge(self):
        """Load all knowledge JSON files"""
        # Load motor issues
        motor_issues_file = self.knowledge_dir / 'motor_issues.json'
        if motor_issues_file.exists():
            try:
                with open(motor_issues_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.motor_issues = data.get('motor_diagnostic_rules', {})
                print(f"✓ Loaded {len(self.motor_issues)} motor diagnostic rules")
            except Exception as e:
                print(f"⚠ Error loading motor_issues.json: {e}")

        # Load calibration guides (if exists)
        cal_guide_file = self.knowledge_dir / 'calibration_guide.json'
        if cal_guide_file.exists():
            try:
                with open(cal_guide_file, 'r', encoding='utf-8') as f:
                    self.calibration_guides = json.load(f)
                print(f"✓ Loaded calibration guides")
            except Exception as e:
                print(f"⚠ Error loading calibration_guide.json: {e}")

        # Load parameter defaults (if exists)
        param_file = self.knowledge_dir / 'parameter_defaults.json'
        if param_file.exists():
            try:
                with open(param_file, 'r', encoding='utf-8') as f:
                    self.parameters = json.load(f)
                print(f"✓ Loaded parameter defaults")
            except Exception as e:
                print(f"⚠ Error loading parameter_defaults.json: {e}")

    def search_motor_issues(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search motor issues by keywords

        Args:
            keywords: List of keywords to search for

        Returns:
            List of matching diagnostic rules
        """
        matches = []

        for issue_id, issue_data in self.motor_issues.items():
            # Check if any keyword matches
            issue_keywords = issue_data.get('keywords', [])

            for keyword in keywords:
                keyword_lower = keyword.lower()
                for issue_keyword in issue_keywords:
                    if keyword_lower in issue_keyword.lower() or issue_keyword.lower() in keyword_lower:
                        # Found a match
                        result = {
                            'id': issue_id,
                            'diagnosis': issue_data.get('diagnosis', 'Unknown'),
                            'severity': issue_data.get('severity', 'medium'),
                            'cause': issue_data.get('cause', ''),
                            'solution_steps': issue_data.get('solution_steps', []),
                            'tips': issue_data.get('tips', []),
                            'related_parameters': issue_data.get('related_parameters', [])
                        }
                        if result not in matches:
                            matches.append(result)
                        break

        return matches

    def search_by_error_message(self, error_message: str) -> List[Dict[str, Any]]:
        """
        Search for solutions based on error message

        Args:
            error_message: Error message from logs (e.g., PreArm error)

        Returns:
            List of matching diagnostic rules
        """
        # Extract keywords from error message
        keywords = error_message.lower().split()

        # Search motor issues
        return self.search_motor_issues(keywords)

    def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific issue by ID

        Args:
            issue_id: Issue identifier

        Returns:
            Issue data or None if not found
        """
        issue_data = self.motor_issues.get(issue_id)
        if issue_data:
            return {
                'id': issue_id,
                'diagnosis': issue_data.get('diagnosis', 'Unknown'),
                'severity': issue_data.get('severity', 'medium'),
                'cause': issue_data.get('cause', ''),
                'solution_steps': issue_data.get('solution_steps', []),
                'tips': issue_data.get('tips', []),
                'related_parameters': issue_data.get('related_parameters', [])
            }
        return None

    def format_solution(self, issue: Dict[str, Any], language: str = 'en') -> str:
        """
        Format issue solution as readable text

        Args:
            issue: Issue dictionary from search results
            language: Language for formatting ('en' or 'ru')

        Returns:
            Formatted solution text
        """
        lines = []

        # Header
        severity_icon = '🔴' if issue['severity'] == 'high' else '🟡' if issue['severity'] == 'medium' else '🟢'
        lines.append(f"{severity_icon} {issue['diagnosis'].upper()}")
        lines.append("=" * 60)

        # Cause
        if language == 'ru':
            lines.append(f"\nПРИЧИНА:")
        else:
            lines.append(f"\nCAUSE:")
        lines.append(f"  {issue['cause']}")

        # Solution steps
        if language == 'ru':
            lines.append(f"\nРЕШЕНИЕ:")
        else:
            lines.append(f"\nSOLUTION:")

        for i, step in enumerate(issue['solution_steps'], 1):
            lines.append(f"  {i}. {step}")

        # Tips
        if issue['tips']:
            if language == 'ru':
                lines.append(f"\nСОВЕТЫ:")
            else:
                lines.append(f"\nTIPS:")

            for tip in issue['tips']:
                lines.append(f"  • {tip}")

        # Related parameters
        if issue['related_parameters']:
            if language == 'ru':
                lines.append(f"\nСВЯЗАННЫЕ ПАРАМЕТРЫ:")
            else:
                lines.append(f"\nRELATED PARAMETERS:")

            lines.append(f"  {', '.join(issue['related_parameters'])}")

        return '\n'.join(lines)

    def get_all_motor_issues(self) -> Dict[str, Dict[str, Any]]:
        """Get all motor issues"""
        return self.motor_issues

    def get_statistics(self) -> Dict[str, int]:
        """
        Get knowledge base statistics

        Returns:
            Dictionary with counts
        """
        return {
            'motor_issues': len(self.motor_issues),
            'calibration_guides': len(self.calibration_guides),
            'parameter_defaults': len(self.parameters)
        }

    def print_summary(self):
        """Print knowledge base summary"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("Knowledge Base Summary")
        print("="*60)
        print(f"Directory: {self.knowledge_dir}")
        print(f"\nLoaded knowledge:")
        print(f"  Motor issues: {stats['motor_issues']}")
        print(f"  Calibration guides: {stats['calibration_guides']}")
        print(f"  Parameter defaults: {stats['parameter_defaults']}")
        print("="*60 + "\n")


# Testing
if __name__ == '__main__':
    print("Testing KnowledgeBase module...\n")

    # Create knowledge base
    kb = KnowledgeBase()

    # Print summary
    kb.print_summary()

    # Test search by error message
    print("\nTest 1: Search by error message 'RC not calibrated'")
    print("-" * 60)
    results = kb.search_by_error_message("RC not calibrated")
    for result in results:
        print(kb.format_solution(result, language='en'))
        print()

    # Test search by keywords
    print("\nTest 2: Search by keywords ['compass', 'calibrat']")
    print("-" * 60)
    results = kb.search_motor_issues(['compass', 'calibrat'])
    for result in results:
        print(kb.format_solution(result, language='ru'))
        print()

    # Test get by ID
    print("\nTest 3: Get specific issue by ID 'rc_not_calibrated'")
    print("-" * 60)
    issue = kb.get_issue_by_id('rc_not_calibrated')
    if issue:
        print(kb.format_solution(issue, language='en'))
