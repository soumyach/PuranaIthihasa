"""Read-only adapter over the existing source graph and its validator."""

import json
import os
import subprocess
import sys
from pathlib import Path

from .errors import ContractError
from .util import tree_hash, tree_snapshot


TABLES = {
    "spines": "story_spines.json",
    "events": "narrative_events.json",
    "passages": "passages.json",
    "evidence": "evidence.json",
    "entities": "entities.json",
    "relationships": "relationships.json",
    "powers": "boons_and_powers.json",
    "variants": "variants_and_conflicts.json",
}


class ReadOnlySourceGraph:
    def __init__(self, graph_root):
        self.root = Path(graph_root)
        if not (self.root / "validate_graph.py").is_file():
            raise ContractError("source graph validator is missing")

    def snapshot(self):
        return tree_snapshot(self.root)

    def graph_hash(self):
        return tree_hash(self.root)

    def _load(self, name):
        path = self.root / TABLES[name]
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def verify(self):
        before = self.snapshot()
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(self.root / "validate_graph.py"), "--root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        after = self.snapshot()
        if before != after:
            raise ContractError("source graph changed while its validator ran")
        try:
            report = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ContractError("source graph validator returned invalid JSON: %s" % exc)
        if completed.returncode != 0 or not report.get("passed"):
            raise ContractError("source graph validation failed", report)
        report["graph_hash"] = tree_hash(self.root)
        return report

    def complete_story_spines(self):
        return sorted(
            (item for item in self._load("spines") if item.get("status") == "COMPLETE"),
            key=lambda item: item["id"],
        )

    @staticmethod
    def _review_records(value):
        records = []
        if isinstance(value, dict):
            if value.get("id"):
                records.append(value)
            else:
                for child in value.values():
                    records.extend(ReadOnlySourceGraph._review_records(child))
        elif isinstance(value, list):
            for child in value:
                records.extend(ReadOnlySourceGraph._review_records(child))
        return records

    def story_packet(self, spine_id):
        spines = {item["id"]: item for item in self._load("spines")}
        spine = spines.get(spine_id)
        if not spine:
            raise ContractError("unknown story spine %s" % spine_id)
        event_index = {item["id"]: item for item in self._load("events")}
        events = [event_index[event_id] for event_id in spine["event_ids"]]
        events.sort(key=lambda item: item["sequence"])
        passage_ids = {value for event in events for value in event.get("passage_ids", [])}
        evidence_ids = {value for event in events for value in event.get("evidence_ids", [])}
        entity_ids = {
            value
            for event in events
            for key in ("participants", "introduced_entity_ids")
            for value in event.get(key, [])
        }
        relationship_ids = {value for event in events for value in event.get("changed_relationship_ids", [])}
        power_ids = {value for event in events for value in event.get("introduced_power_ids", [])}
        passages = [item for item in self._load("passages") if item["id"] in passage_ids]
        evidence = [item for item in self._load("evidence") if item["id"] in evidence_ids]
        entities = [item for item in self._load("entities") if item["id"] in entity_ids]
        relationships = [
            item for item in self._load("relationships")
            if item["id"] in relationship_ids or item.get("subject_id") in entity_ids or item.get("object_id") in entity_ids
        ]
        powers = [
            item for item in self._load("powers")
            if item["id"] in power_ids
            or item.get("recipient_id") in entity_ids
            or item.get("grantor_id") in entity_ids
            or set(item.get("later_event_ids", [])).intersection(spine["event_ids"])
        ]
        variants = [item for item in self._load("variants") if spine["source_id"] in item.get("source_ids", [])]
        with (self.root / "claims_needing_review.json").open("r", encoding="utf-8") as handle:
            reviews = self._review_records(json.load(handle))
        unresolved = [
            item for item in reviews
            if item.get("source_id") == spine["source_id"]
            or item.get("id") in evidence_ids
            or item.get("id") in relationship_ids
            or item.get("id") in power_ids
            or item.get("id") in spine["event_ids"]
        ]
        return {
            "graph_hash": self.graph_hash(),
            "spine": spine,
            "events": events,
            "passages": passages,
            "evidence": evidence,
            "entities": entities,
            "relationships": relationships,
            "boons_and_powers": powers,
            "variants_and_conflicts": variants,
            "unresolved_review_flags": unresolved,
            "completeness": {
                "bounded_spine_status": spine["status"],
                "basis": spine.get("completeness_basis"),
                "not_exhaustive_scripture_verification": True,
            },
        }

    def assert_unchanged(self, snapshot):
        current = self.snapshot()
        if current != snapshot:
            changed = sorted(set(snapshot).symmetric_difference(current) | {
                key for key in set(snapshot).intersection(current) if snapshot[key] != current[key]
            })
            raise ContractError("read-only source graph guard failed", {"changed": changed})
        return True
