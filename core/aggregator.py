"""
SP3CT3R Aggregator
Combines findings from multiple modules into a unified entity profile
"""
from typing import List, Dict, Any
from collections import defaultdict


class EntityAggregator:
    """Builds a unified intelligence profile from multi-module scan results."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}

    def ingest(self, target: str, module: str, results: List[Dict]) -> Dict:
        if target not in self.profiles:
            self.profiles[target] = {
                "target": target, "modules_run": [], "findings": [],
                "risk_level": "info", "categories": defaultdict(list),
            }
        profile = self.profiles[target]
        if module not in profile["modules_run"]:
            profile["modules_run"].append(module)
        profile["findings"].extend(results)
        for r in results:
            profile["categories"][r.get("category", "general")].append(r)
        profile["risk_level"] = self._compute_risk(profile["findings"])
        return profile

    def _compute_risk(self, findings: List[Dict]) -> str:
        levels = [f.get("risk_level", "info") for f in findings]
        for lvl in ["critical", "high", "medium", "low"]:
            if lvl in levels:
                return lvl
        return "info"

    def get_profile(self, target: str) -> Dict:
        return self.profiles.get(target, {})

    def summary_stats(self, target: str) -> Dict:
        profile = self.get_profile(target)
        if not profile:
            return {}
        findings = profile.get("findings", [])
        return {
            "total_findings": len(findings),
            "found": sum(1 for f in findings if f.get("status") == "found"),
            "exposed": sum(1 for f in findings if f.get("status") == "exposed"),
            "risk_level": profile.get("risk_level"),
            "modules": profile.get("modules_run"),
            "categories": list(profile.get("categories", {}).keys()),
        }