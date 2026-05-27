"""
SP3CT3R Entity Correlator
Links findings across modules to build relationship graphs
"""
from typing import List, Dict, Any, Set, Tuple


class EntityCorrelator:
    """
    Identifies connections between entities across scan modules.
    Powers the Graph View visualization.
    """

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}  # id -> node data
        self.edges: List[Dict] = []       # list of {source, target, label, weight}

    def add_finding(self, finding: Dict, scan_module: str):
        """Extract entities from a finding and add to graph."""
        data = finding.get("data", "")
        platform = finding.get("platform", "")
        category = finding.get("category", "")

        # Add node for the platform/service
        node_id = f"{category}:{platform}"
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id, "label": platform,
                "type": category, "module": scan_module,
                "risk": finding.get("risk_level", "info"),
            }

        # Extract IP addresses and link them
        import re
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', data)
        for ip in ips:
            ip_id = f"ip:{ip}"
            if ip_id not in self.nodes:
                self.nodes[ip_id] = {"id": ip_id, "label": ip, "type": "ip", "module": scan_module, "risk": "info"}
            self.edges.append({"source": node_id, "target": ip_id, "label": "resolves_to", "weight": 1})

        # Extract domains
        domains = re.findall(r'\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', data)
        for domain in domains[:5]:
            d_id = f"domain:{domain}"
            if d_id not in self.nodes:
                self.nodes[d_id] = {"id": d_id, "label": domain, "type": "domain", "module": scan_module, "risk": "info"}
            self.edges.append({"source": node_id, "target": d_id, "label": "related_to", "weight": 1})

    def get_graph(self) -> Dict:
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }