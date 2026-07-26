#!/usr/bin/env python3
"""Initialize, validate, and deterministically compile architecture discovery models."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

SCHEMA_VERSION = 1
UNIT_KINDS = {"runtime", "store", "channel", "library", "external", "person"}
SCAN_STATUSES = {"complete", "partial", "blocked"}
INBOUND_KINDS = {"http", "grpc", "event", "message", "job", "ui", "file", "other"}
OUTBOUND_KINDS = {"request", "event", "message", "data", "search", "file", "library", "ui-load", "other"}
CERTAINTIES = {"observed", "corroborated", "inferred", "conflicting", "unknown"}


class ModelError(ValueError):
    """Raised when a discovery artifact violates the model contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ModelError(f"{path}: top-level JSON value must be an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def require_string(value: Any, where: str, failures: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{where} must be a non-empty string")


def validate_evidence(items: Any, where: str, failures: list[str], required: bool = True) -> None:
    if not isinstance(items, list) or (required and not items):
        failures.append(f"{where} must be a{' non-empty' if required else ''} array")
        return
    for index, item in enumerate(items):
        item_where = f"{where}[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{item_where} must be an object")
            continue
        require_string(item.get("path"), f"{item_where}.path", failures)
        require_string(item.get("observation"), f"{item_where}.observation", failures)
        if "lineStart" in item and (not isinstance(item["lineStart"], int) or item["lineStart"] < 1):
            failures.append(f"{item_where}.lineStart must be a positive integer")
        if "lineEnd" in item and (not isinstance(item["lineEnd"], int) or item["lineEnd"] < item.get("lineStart", 1)):
            failures.append(f"{item_where}.lineEnd must be at or after lineStart")


def validate_contract(contract: Any, where: str, failures: list[str]) -> None:
    if not isinstance(contract, dict):
        failures.append(f"{where} must be an object")
        return
    require_string(contract.get("name"), f"{where}.name", failures)
    for field in ("version", "schemaPath", "fingerprint", "format"):
        if field in contract:
            require_string(contract[field], f"{where}.{field}", failures)
    if "keyFields" in contract and (not isinstance(contract["keyFields"], list) or not all(isinstance(item, str) and item for item in contract["keyFields"])):
        failures.append(f"{where}.keyFields must be an array of non-empty strings")


def validate_scan(scan: dict[str, Any], label: str = "scan") -> list[str]:
    failures: list[str] = []
    if scan.get("schemaVersion") != SCHEMA_VERSION:
        failures.append(f"{label}.schemaVersion must equal {SCHEMA_VERSION}")
    source = scan.get("source")
    if not isinstance(source, dict):
        failures.append(f"{label}.source must be an object")
        source = {}
    for field in ("id", "path", "revision"):
        require_string(source.get(field), f"{label}.source.{field}", failures)
    if source.get("scanStatus") not in SCAN_STATUSES:
        failures.append(f"{label}.source.scanStatus must be one of {sorted(SCAN_STATUSES)}")
    if "coverage" in source and not isinstance(source["coverage"], dict):
        failures.append(f"{label}.source.coverage must be an object")

    units = scan.get("units")
    if not isinstance(units, dict):
        failures.append(f"{label}.units must be an object keyed by local unit ID")
        units = {}
    interface_ids: dict[str, set[str]] = {}
    outbound_ids: dict[str, set[str]] = {}
    for unit_id, unit in units.items():
        where = f"{label}.units.{unit_id}"
        require_string(unit_id, f"{where} key", failures)
        if not isinstance(unit, dict):
            failures.append(f"{where} must be an object")
            continue
        if unit.get("kind") not in UNIT_KINDS:
            failures.append(f"{where}.kind must be one of {sorted(UNIT_KINDS)}")
        for field in ("name", "responsibility"):
            require_string(unit.get(field), f"{where}.{field}", failures)
        technology = unit.get("technology", [])
        if not isinstance(technology, list) or not all(isinstance(item, str) and item for item in technology):
            failures.append(f"{where}.technology must be an array of non-empty strings")
        if unit.get("kind") in {"runtime", "store"} and not technology:
            failures.append(f"{where}.technology is required for runtimes and stores; use Unknown when unavailable")
        identity = unit.get("identity", {})
        if not isinstance(identity, dict):
            failures.append(f"{where}.identity must be an object")
        validate_evidence(unit.get("evidence"), f"{where}.evidence", failures)

        inbound = unit.get("inbound", [])
        if not isinstance(inbound, list):
            failures.append(f"{where}.inbound must be an array")
            inbound = []
        seen_inbound: set[str] = set()
        for index, interface in enumerate(inbound):
            item_where = f"{where}.inbound[{index}]"
            if not isinstance(interface, dict):
                failures.append(f"{item_where} must be an object")
                continue
            interface_id = interface.get("id")
            require_string(interface_id, f"{item_where}.id", failures)
            if interface_id in seen_inbound:
                failures.append(f"{where}.inbound contains duplicate id {interface_id!r}")
            if isinstance(interface_id, str):
                seen_inbound.add(interface_id)
            if interface.get("kind") not in INBOUND_KINDS:
                failures.append(f"{item_where}.kind must be one of {sorted(INBOUND_KINDS)}")
            require_string(interface.get("purpose"), f"{item_where}.purpose", failures)
            if interface.get("kind") == "http":
                require_string(interface.get("method"), f"{item_where}.method", failures)
                require_string(interface.get("path"), f"{item_where}.path", failures)
            if interface.get("kind") in {"event", "message"}:
                channel = interface.get("channel")
                if not isinstance(channel, dict) or not channel:
                    failures.append(f"{item_where}.channel is required for event/message interfaces")
                elif not any(channel.get(field) for field in ("name", "topic", "queue", "channel")):
                    failures.append(f"{item_where}.channel must identify a name, topic, or queue")
            if "contract" in interface:
                validate_contract(interface["contract"], f"{item_where}.contract", failures)
            if "rules" in interface and (not isinstance(interface["rules"], list) or not all(isinstance(item, str) and item for item in interface["rules"])):
                failures.append(f"{item_where}.rules must be an array of non-empty strings")
            validate_evidence(interface.get("evidence"), f"{item_where}.evidence", failures)
        interface_ids[unit_id] = seen_inbound

        outbound = unit.get("outbound", [])
        if not isinstance(outbound, list):
            failures.append(f"{where}.outbound must be an array")
            outbound = []
        seen_outbound: set[str] = set()
        for index, dependency in enumerate(outbound):
            item_where = f"{where}.outbound[{index}]"
            if not isinstance(dependency, dict):
                failures.append(f"{item_where} must be an object")
                continue
            dependency_id = dependency.get("id")
            require_string(dependency_id, f"{item_where}.id", failures)
            if dependency_id in seen_outbound:
                failures.append(f"{where}.outbound contains duplicate id {dependency_id!r}")
            if isinstance(dependency_id, str):
                seen_outbound.add(dependency_id)
            if dependency.get("kind") not in OUTBOUND_KINDS:
                failures.append(f"{item_where}.kind must be one of {sorted(OUTBOUND_KINDS)}")
            require_string(dependency.get("purpose"), f"{item_where}.purpose", failures)
            require_string(dependency.get("technology"), f"{item_where}.technology", failures)
            target = dependency.get("target")
            if not isinstance(target, dict) or not target:
                failures.append(f"{item_where}.target must be a non-empty object")
            elif not target.get("unitId") and not target.get("canonicalId"):
                if target.get("kind") not in UNIT_KINDS:
                    failures.append(f"{item_where}.target.kind must classify a non-local target")
                expected_kinds = {
                    "request": {"runtime", "external"},
                    "event": {"channel"},
                    "message": {"channel"},
                    "data": {"store"},
                    "search": {"store", "runtime", "external"},
                    "library": {"library"},
                    "ui-load": {"runtime", "external"},
                }.get(dependency.get("kind"))
                if expected_kinds and target.get("kind") not in expected_kinds:
                    failures.append(f"{item_where}.target.kind must be one of {sorted(expected_kinds)} for {dependency.get('kind')}")
            if "contract" in dependency:
                validate_contract(dependency["contract"], f"{item_where}.contract", failures)
            if "rules" in dependency and (not isinstance(dependency["rules"], list) or not all(isinstance(item, str) and item for item in dependency["rules"])):
                failures.append(f"{item_where}.rules must be an array of non-empty strings")
            validate_evidence(dependency.get("evidence"), f"{item_where}.evidence", failures)
        outbound_ids[unit_id] = seen_outbound

    operations = scan.get("operations", {})
    if not isinstance(operations, dict):
        failures.append(f"{label}.operations must be an object keyed by operation ID")
        operations = {}
    for operation_id, operation in operations.items():
        where = f"{label}.operations.{operation_id}"
        if not isinstance(operation, dict):
            failures.append(f"{where} must be an object")
            continue
        require_string(operation.get("name"), f"{where}.name", failures)
        owner = operation.get("owner")
        if owner not in units:
            failures.append(f"{where}.owner must reference a unit in this scan")
        trigger = operation.get("trigger")
        if trigger is not None and trigger not in interface_ids.get(owner, set()):
            failures.append(f"{where}.trigger must reference an inbound interface on the owner")
        steps = operation.get("steps")
        if not isinstance(steps, list) or not steps:
            failures.append(f"{where}.steps must be a non-empty array")
            continue
        orders: list[int] = []
        for index, step in enumerate(steps):
            step_where = f"{where}.steps[{index}]"
            if not isinstance(step, dict):
                failures.append(f"{step_where} must be an object")
                continue
            order = step.get("order")
            if not isinstance(order, int) or order < 1:
                failures.append(f"{step_where}.order must be a positive integer")
            else:
                orders.append(order)
            require_string(step.get("action"), f"{step_where}.action", failures)
            at = step.get("at")
            uses = step.get("uses")
            if (at is None) == (uses is None):
                failures.append(f"{step_where} must contain exactly one of at or uses")
            if at is not None and at not in units:
                failures.append(f"{step_where}.at must reference a unit in this scan")
            if uses is not None and uses not in outbound_ids.get(owner, set()):
                failures.append(f"{step_where}.uses must reference an outbound dependency on the operation owner")
            if "next" in step and not isinstance(step["next"], (int, str, list, dict)):
                failures.append(f"{step_where}.next must be an order, end marker, array, or condition map")
            validate_evidence(step.get("evidence"), f"{step_where}.evidence", failures)
        if orders and sorted(orders) != list(range(1, len(orders) + 1)):
            failures.append(f"{where}.steps orders must be unique and contiguous from 1")

    gaps = scan.get("gaps", [])
    if not isinstance(gaps, list):
        failures.append(f"{label}.gaps must be an array")
    else:
        seen_gaps: set[str] = set()
        for index, gap in enumerate(gaps):
            where = f"{label}.gaps[{index}]"
            if not isinstance(gap, dict):
                failures.append(f"{where} must be an object")
                continue
            for field in ("id", "description", "impact"):
                require_string(gap.get(field), f"{where}.{field}", failures)
            if gap.get("id") in seen_gaps:
                failures.append(f"{label}.gaps contains duplicate id {gap.get('id')!r}")
            if isinstance(gap.get("id"), str):
                seen_gaps.add(gap["id"])
            searches = gap.get("searches")
            if not isinstance(searches, list) or not all(isinstance(item, str) and item for item in searches):
                failures.append(f"{where}.searches must be an array of non-empty strings")
    return failures


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:60] or "unknown"


def stable_suffix(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:10]


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(value[key]) for key in sorted(value) if value[key] not in (None, "", [], {})}
    return value


def identity_key(kind: str, identity: dict[str, Any], fallback: str) -> tuple[str, str]:
    identity = normalize(identity)
    if identity.get("canonicalId"):
        return "canonical", identity["canonicalId"]
    if kind == "runtime" and identity.get("deploymentIdentity"):
        return "runtime", identity["deploymentIdentity"]
    if kind == "store" and any(identity.get(field) for field in ("server", "database", "schema", "index", "bucket")):
        selected = {field: identity[field] for field in ("technology", "server", "database", "schema", "index", "bucket") if field in identity}
        return "store", json.dumps(selected, sort_keys=True, separators=(",", ":"))
    if kind == "channel" and any(identity.get(field) for field in ("name", "topic", "queue")):
        selected = {field: identity[field] for field in ("transport", "namespace", "name", "topic", "queue") if field in identity}
        return "channel", json.dumps(selected, sort_keys=True, separators=(",", ":"))
    if kind == "library" and identity.get("package"):
        return "library", json.dumps({field: identity[field] for field in ("package", "version") if field in identity}, sort_keys=True)
    if kind in {"external", "person"} and any(identity.get(field) for field in ("address", "name")):
        return kind, json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return "local", fallback


def node_id_for(kind: str, key: tuple[str, str], name: str) -> str:
    key_type, key_value = key
    if key_type == "canonical":
        return key_value
    readable = name
    if key_type == "runtime":
        readable = key_value
    elif key_type in {"store", "channel", "library"}:
        try:
            values = json.loads(key_value)
            readable = values.get("database") or values.get("schema") or values.get("index") or values.get("topic") or values.get("queue") or values.get("name") or values.get("package") or name
        except json.JSONDecodeError:
            pass
    return f"{kind}.{slug(str(readable))}.{stable_suffix([kind, key])}"


def evidence_with_source(items: list[dict[str, Any]], source: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in items:
        enriched = deepcopy(item)
        enriched["sourceId"] = source["id"]
        enriched["revision"] = source["revision"]
        result.append(enriched)
    return result


def target_kind(dependency: dict[str, Any]) -> str:
    target = dependency.get("target", {})
    if target.get("kind") in UNIT_KINDS:
        return target["kind"]
    return {
        "data": "store",
        "search": "store",
        "event": "channel",
        "message": "channel",
        "library": "library",
    }.get(dependency.get("kind"), "external")


def target_identity(dependency: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(dependency.get("target", {}))
    target.pop("unitId", None)
    target.pop("canonicalId", None)
    target.pop("kind", None)
    if dependency.get("kind") in {"event", "message"}:
        if "channel" in target and "name" not in target:
            target["name"] = target.pop("channel")
    return target


def target_name(dependency: dict[str, Any]) -> str:
    target = dependency.get("target", {})
    return str(target.get("name") or target.get("deploymentIdentity") or target.get("database") or target.get("schema") or target.get("index") or target.get("topic") or target.get("queue") or target.get("channel") or target.get("address") or "Unknown dependency")


def contract_compatible(left: Any, right: Any) -> bool:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return True
    for field in ("name", "version", "fingerprint"):
        if left.get(field) and right.get(field) and normalize(left[field]) != normalize(right[field]):
            return False
    return True


def contract_matches(left: Any, right: Any) -> bool:
    if not isinstance(left, dict) or not isinstance(right, dict) or not left.get("name") or not right.get("name"):
        return False
    for field in ("name", "version", "fingerprint"):
        if left.get(field) or right.get(field):
            if not left.get(field) or not right.get(field) or normalize(left[field]) != normalize(right[field]):
                return False
    return True


def interface_endpoint_matches(dependency: dict[str, Any], interface: dict[str, Any]) -> bool:
    kind = dependency.get("kind")
    if kind == "request" and interface.get("kind") not in {"http", "grpc", "ui", "other"}:
        return False
    desired = dependency.get("interface", {})
    for dep_field, iface_field in (("method", "method"), ("path", "path")):
        if desired.get(dep_field) and normalize(desired[dep_field]) != normalize(interface.get(iface_field)):
            return False
    return True


def interface_matches(dependency: dict[str, Any], interface: dict[str, Any]) -> bool:
    if not interface_endpoint_matches(dependency, interface):
        return False
    desired = dependency.get("interface", {})
    if desired.get("version") and normalize(desired["version"]) != normalize(interface.get("version")):
        return False
    if dependency.get("contract") and not contract_matches(dependency["contract"], interface.get("contract")):
        return False
    return True


def interface_conflicts(dependency: dict[str, Any], interface: dict[str, Any]) -> bool:
    if not interface_endpoint_matches(dependency, interface):
        return False
    desired_version = dependency.get("interface", {}).get("version")
    observed_version = interface.get("version")
    if desired_version and observed_version and normalize(desired_version) != normalize(observed_version):
        return True
    return not contract_compatible(dependency.get("contract"), interface.get("contract"))


def channel_identity(channel: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(channel)
    if "channel" in result and "name" not in result:
        result["name"] = result.pop("channel")
    return result


def compile_model(model_dir: Path) -> dict[str, Any]:
    subject = load_json(model_dir / "subject.json")
    decisions = load_json(model_dir / "decisions.json")
    scans: list[tuple[Path, dict[str, Any]]] = []
    failures: list[str] = []
    for path in sorted((model_dir / "scans").glob("*.json")):
        scan = load_json(path)
        failures.extend(validate_scan(scan, path.name))
        scans.append((path, scan))
    if failures:
        raise ModelError("scan validation failed:\n- " + "\n- ".join(failures))

    overrides = decisions.get("identityOverrides", {})
    if not isinstance(overrides, dict):
        raise ModelError("decisions.identityOverrides must be an object")
    target_overrides = decisions.get("targetOverrides", {})
    if not isinstance(target_overrides, dict):
        raise ModelError("decisions.targetOverrides must be an object")

    nodes: dict[str, dict[str, Any]] = {}
    key_index: dict[tuple[str, str], str] = {}
    local_to_node: dict[tuple[str, str], str] = {}
    unit_observations: dict[str, list[tuple[dict[str, Any], str, dict[str, Any]]]] = {}
    conflicts: dict[str, dict[str, Any]] = {}
    gaps: dict[str, dict[str, Any]] = {}

    def register_node(kind: str, name: str, identity: dict[str, Any], fallback: str, observation: dict[str, Any] | None = None, source: dict[str, Any] | None = None, source_ref: str | None = None) -> str:
        override = overrides.get(source_ref, None) if source_ref else None
        if override:
            key = ("canonical", override)
        else:
            key = identity_key(kind, identity, fallback)
        node_id = key_index.get(key)
        if node_id is None:
            node_id = node_id_for(kind, key, name)
            key_index[key] = node_id
            if node_id not in nodes:
                nodes[node_id] = {
                    "name": name,
                    "kind": kind,
                    "subtype": observation.get("subtype") if observation else None,
                    "responsibility": observation.get("responsibility", "Unknown") if observation else "Unknown",
                    "technology": sorted(set(observation.get("technology", []))) if observation else [],
                    "identity": deepcopy(identity),
                    "ownership": observation.get("ownership") if observation else None,
                    "sourceRefs": [],
                    "evidence": [],
                    "candidate": observation is None,
                }
        if observation is not None and source is not None and source_ref is not None:
            node = nodes[node_id]
            node["candidate"] = False
            node["sourceRefs"].append(source_ref)
            node["evidence"].extend(evidence_with_source(observation.get("evidence", []), source))
            node["technology"] = sorted(set(node["technology"]) | set(observation.get("technology", [])))
            unit_observations.setdefault(node_id, []).append((source, source_ref, observation))
        return node_id

    for _, scan in scans:
        source = scan["source"]
        for local_id, unit in sorted(scan["units"].items()):
            source_ref = f"{source['id']}:{local_id}"
            node_id = register_node(unit["kind"], unit["name"], unit.get("identity", {}), source_ref, unit, source, source_ref)
            local_to_node[(source["id"], local_id)] = node_id

    # Report incompatible observations merged through the same strong identity.
    for node_id, observations in sorted(unit_observations.items()):
        names = sorted({item[2]["name"] for item in observations})
        kinds = sorted({item[2]["kind"] for item in observations})
        subtypes = sorted({item[2].get("subtype") for item in observations if item[2].get("subtype")})
        ownership = sorted({json.dumps(item[2].get("ownership"), sort_keys=True) for item in observations if item[2].get("ownership") is not None})
        differences = {}
        if len(names) > 1:
            differences["names"] = names
        if len(kinds) > 1:
            differences["kinds"] = kinds
        if len(subtypes) > 1:
            differences["subtypes"] = subtypes
        if len(ownership) > 1:
            differences["ownership"] = [json.loads(item) for item in ownership]
        if differences:
            conflict_id = f"conflict.identity.{slug(node_id)}"
            conflicts[conflict_id] = {"scope": node_id, "kind": "identity", "description": "Merged observations disagree", "details": differences}

    interfaces: dict[str, dict[str, Any]] = {}
    inbound_by_node: dict[str, list[tuple[str, dict[str, Any], dict[str, Any], str]]] = {}
    for _, scan in scans:
        source = scan["source"]
        for local_id, unit in sorted(scan["units"].items()):
            owner = local_to_node[(source["id"], local_id)]
            for interface in unit.get("inbound", []):
                interface_id = f"iface.{slug(owner)}.{slug(interface['id'])}.{stable_suffix([source['id'], local_id, interface['id']])}"
                interfaces[interface_id] = {
                    **{key: deepcopy(value) for key, value in interface.items() if key != "evidence"},
                    "owner": owner,
                    "sourceRef": f"{source['id']}:{local_id}:{interface['id']}",
                    "evidence": evidence_with_source(interface["evidence"], source),
                }
                inbound_by_node.setdefault(owner, []).append((interface_id, interface, source, local_id))

    relationships: dict[str, dict[str, Any]] = {}
    relationship_index: dict[str, str] = {}
    outbound_to_relationship: dict[tuple[str, str, str], str] = {}

    def add_relationship(suggested_id: str, relationship: dict[str, Any]) -> str:
        identity = json.dumps(normalize({
            "from": relationship["from"],
            "to": relationship["to"],
            "kind": relationship["kind"],
            "purpose": relationship["purpose"],
            "technology": relationship["technology"],
            "contract": relationship.get("contract"),
            "interface": relationship.get("interface"),
            "destinationInterface": relationship.get("destinationInterface"),
        }), sort_keys=True, separators=(",", ":"))
        existing_id = relationship_index.get(identity)
        if existing_id is None:
            relationship_index[identity] = suggested_id
            relationships[suggested_id] = relationship
            return suggested_id
        existing = relationships[existing_id]
        existing["sourceFindings"] = sorted(set(existing["sourceFindings"]) | set(relationship["sourceFindings"]))
        known_evidence = {json.dumps(item, sort_keys=True) for item in existing["evidence"]}
        existing["evidence"].extend(item for item in relationship["evidence"] if json.dumps(item, sort_keys=True) not in known_evidence)
        if existing["certainty"] == "observed" and relationship["certainty"] in {"observed", "corroborated"}:
            existing["certainty"] = "corroborated"
        return existing_id

    def ensure_target_node(dependency: dict[str, Any], source: dict[str, Any], owner_local: str) -> str:
        target = dependency["target"]
        override_ref = f"{source['id']}:{owner_local}:{dependency['id']}"
        if override_ref in target_overrides:
            canonical = target_overrides[override_ref]
            node_id = register_node(target_kind(dependency), target_name(dependency), {"canonicalId": canonical}, override_ref)
        elif target.get("canonicalId"):
            node_id = register_node(target_kind(dependency), target_name(dependency), {"canonicalId": target["canonicalId"]}, override_ref)
        elif target.get("unitId"):
            local_key = (source["id"], target["unitId"])
            if local_key not in local_to_node:
                raise ModelError(f"{override_ref} targets unknown local unit {target['unitId']!r}")
            node_id = local_to_node[local_key]
        else:
            kind = target_kind(dependency)
            identity = target_identity(dependency)
            key = identity_key(kind, identity, override_ref)
            node_id = key_index.get(key) or register_node(kind, target_name(dependency), identity, override_ref)
        node = nodes[node_id]
        if override_ref not in node["sourceRefs"]:
            node["sourceRefs"].append(override_ref)
            node["evidence"].extend(evidence_with_source(dependency["evidence"], source))
        return node_id

    for _, scan in scans:
        source = scan["source"]
        for local_id, unit in sorted(scan["units"].items()):
            from_node = local_to_node[(source["id"], local_id)]
            for dependency in unit.get("outbound", []):
                to_node = ensure_target_node(dependency, source, local_id)
                finding_ref = f"{source['id']}:{local_id}:{dependency['id']}"
                relationship_id = f"rel.{slug(from_node)}.{slug(dependency['id'])}.{stable_suffix(finding_ref)}"
                target_interfaces = inbound_by_node.get(to_node, [])
                matches = [item for item in target_interfaces if interface_matches(dependency, item[1])]
                incompatible = [item for item in target_interfaces if interface_conflicts(dependency, item[1])]
                certainty = "corroborated" if matches else ("conflicting" if incompatible else "observed")
                relationship = {
                    "from": from_node,
                    "to": to_node,
                    "kind": dependency["kind"],
                    "purpose": dependency["purpose"],
                    "technology": dependency["technology"],
                    "contract": deepcopy(dependency.get("contract")),
                    "interface": deepcopy(dependency.get("interface")),
                    "rules": deepcopy(dependency.get("rules", [])),
                    "certainty": certainty,
                    "sourceFindings": [finding_ref],
                    "evidence": evidence_with_source(dependency["evidence"], source),
                }
                if matches:
                    relationship["destinationInterface"] = matches[0][0]
                    relationship["sourceFindings"].append(f"{matches[0][2]['id']}:{matches[0][3]}:{matches[0][1]['id']}")
                    relationship["evidence"].extend(evidence_with_source(matches[0][1]["evidence"], matches[0][2]))
                relationship_id = add_relationship(relationship_id, relationship)
                outbound_to_relationship[(source["id"], local_id, dependency["id"])] = relationship_id
                if incompatible:
                    conflict_id = f"conflict.interface.{slug(finding_ref)}"
                    conflicts[conflict_id] = {
                        "scope": relationship_id,
                        "kind": "interface-version",
                        "description": "Outbound and inbound interface identities are incompatible",
                        "sourceFinding": finding_ref,
                        "destinationInterfaces": [item[0] for item in incompatible],
                    }
                if nodes[to_node]["candidate"] and target_kind(dependency) not in {"store", "channel", "library"}:
                    gap_id = f"gap.unresolved-target.{slug(finding_ref)}"
                    gaps[gap_id] = {
                        "scope": relationship_id,
                        "kind": "unresolved-target",
                        "description": f"No scanned unit matches outbound target {target_name(dependency)!r}",
                        "impact": "The external identity and ownership are unconfirmed",
                        "sourceFindings": [finding_ref],
                    }

    # Event/message inbound interfaces establish channel -> consumer direction.
    channel_contracts: dict[str, dict[str, list[tuple[str, dict[str, Any] | None]]]] = {}
    for owner, entries in sorted(inbound_by_node.items()):
        for interface_id, interface, source, local_id in entries:
            if interface.get("kind") not in {"event", "message"}:
                continue
            identity = channel_identity(interface["channel"])
            channel_name = str(identity.get("name") or identity.get("topic") or identity.get("queue") or "Message channel")
            channel_ref = f"{source['id']}:{local_id}:{interface['id']}:channel"
            channel_node = register_node("channel", channel_name, identity, channel_ref)
            if channel_ref not in nodes[channel_node]["sourceRefs"]:
                nodes[channel_node]["sourceRefs"].append(channel_ref)
                nodes[channel_node]["evidence"].extend(evidence_with_source(interface["evidence"], source))
            finding_ref = f"{source['id']}:{local_id}:{interface['id']}"
            relationship_id = f"rel.{slug(channel_node)}.{slug(owner)}.{stable_suffix(finding_ref)}"
            relationship_id = add_relationship(relationship_id, {
                "from": channel_node,
                "to": owner,
                "kind": "message-delivery",
                "purpose": interface["purpose"],
                "technology": str(interface["channel"].get("technology") or interface["channel"].get("transport") or "Unknown"),
                "contract": deepcopy(interface.get("contract")),
                "destinationInterface": interface_id,
                "rules": deepcopy(interface.get("rules", [])),
                "certainty": "observed",
                "sourceFindings": [finding_ref],
                "evidence": evidence_with_source(interface["evidence"], source),
            })
            contract_name = normalize(interface.get("contract", {}).get("name", "unknown"))
            channel_contracts.setdefault(channel_node, {}).setdefault(contract_name, []).append((relationship_id, interface.get("contract")))

    for relationship_id, relationship in relationships.items():
        if relationship["kind"] in {"event", "message"} and nodes[relationship["to"]]["kind"] == "channel":
            contract_name = normalize((relationship.get("contract") or {}).get("name", "unknown"))
            channel_contracts.setdefault(relationship["to"], {}).setdefault(contract_name, []).append((relationship_id, relationship.get("contract")))

    for channel_node, contracts_by_name in sorted(channel_contracts.items()):
        for contract_name, entries in sorted(contracts_by_name.items()):
            compatible = True
            for _, left in entries:
                for _, right in entries:
                    if not contract_compatible(left, right):
                        compatible = False
            fully_matched = all(contract_matches(left, right) for _, left in entries for _, right in entries)
            if compatible and fully_matched and len(entries) > 1:
                for relationship_id, _ in entries:
                    relationships[relationship_id]["certainty"] = "corroborated"
            elif not compatible:
                conflict_id = f"conflict.contract.{slug(channel_node)}.{slug(str(contract_name))}"
                ordered_entries = sorted(entries, key=lambda item: item[0])
                conflicts[conflict_id] = {
                    "scope": channel_node,
                    "kind": "contract-version",
                    "description": "Publishers and consumers on the same channel use incompatible contract identities",
                    "relationships": [item[0] for item in ordered_entries],
                    "contracts": [item[1] for item in ordered_entries],
                }
                for relationship_id, _ in entries:
                    relationships[relationship_id]["certainty"] = "conflicting"

    flows: dict[str, dict[str, Any]] = {}
    for _, scan in scans:
        source = scan["source"]
        for operation_id, operation in sorted(scan.get("operations", {}).items()):
            owner = local_to_node[(source["id"], operation["owner"])]
            flow_id = f"flow.{slug(owner)}.{slug(operation_id)}.{stable_suffix([source['id'], operation_id])}"
            steps = []
            for step in operation["steps"]:
                rendered = {key: deepcopy(value) for key, value in step.items() if key not in {"at", "uses", "evidence"}}
                if "at" in step:
                    rendered["at"] = local_to_node[(source["id"], step["at"])]
                else:
                    rendered["relationship"] = outbound_to_relationship[(source["id"], operation["owner"], step["uses"])]
                rendered["evidence"] = evidence_with_source(step["evidence"], source)
                steps.append(rendered)
            trigger_interface = None
            if operation.get("trigger"):
                candidates = [item for item in inbound_by_node.get(owner, []) if item[1]["id"] == operation["trigger"] and item[2]["id"] == source["id"]]
                if candidates:
                    trigger_interface = candidates[0][0]
            flows[flow_id] = {
                "name": operation["name"],
                "owner": owner,
                "trigger": trigger_interface,
                "steps": steps,
                "sourceRef": f"{source['id']}:{operation_id}",
            }

    for _, scan in scans:
        source = scan["source"]
        for gap in scan.get("gaps", []):
            gap_id = f"gap.{slug(source['id'])}.{slug(gap['id'])}"
            gaps[gap_id] = {**deepcopy(gap), "sourceId": source["id"], "revision": source["revision"]}

    for node in nodes.values():
        node["sourceRefs"] = sorted(set(node["sourceRefs"]))
        node["evidence"] = [json.loads(item) for item in sorted({json.dumps(value, sort_keys=True) for value in node["evidence"]})]
    for relationship in relationships.values():
        relationship["sourceFindings"] = sorted(set(relationship["sourceFindings"]))
        relationship["evidence"] = [json.loads(item) for item in sorted({json.dumps(value, sort_keys=True) for value in relationship["evidence"]})]

    boundaries = deepcopy(decisions.get("systemBoundaries", {}))
    canonical = {
        "schemaVersion": SCHEMA_VERSION,
        "subject": deepcopy(subject.get("subject", subject)),
        "sources": {scan["source"]["id"]: deepcopy(scan["source"]) for _, scan in scans},
        "nodes": {key: {k: v for k, v in value.items() if v is not None} for key, value in sorted(nodes.items())},
        "interfaces": {key: value for key, value in sorted(interfaces.items())},
        "relationships": {key: {k: v for k, v in value.items() if v is not None} for key, value in sorted(relationships.items())},
        "flows": {key: value for key, value in sorted(flows.items())},
        "systemBoundaries": boundaries,
        "gaps": {key: value for key, value in sorted(gaps.items())},
        "conflicts": {key: value for key, value in sorted(conflicts.items())},
    }
    failures = validate_canonical(canonical)
    if failures:
        raise ModelError("compiled canonical model is invalid:\n- " + "\n- ".join(failures))
    return canonical


def validate_canonical(model: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if model.get("schemaVersion") != SCHEMA_VERSION:
        failures.append(f"canonical.schemaVersion must equal {SCHEMA_VERSION}")
    for field in ("nodes", "interfaces", "relationships", "flows", "gaps", "conflicts", "systemBoundaries"):
        if not isinstance(model.get(field), dict):
            failures.append(f"canonical.{field} must be an object")
    nodes = model.get("nodes", {}) if isinstance(model.get("nodes"), dict) else {}
    interfaces = model.get("interfaces", {}) if isinstance(model.get("interfaces"), dict) else {}
    relationships = model.get("relationships", {}) if isinstance(model.get("relationships"), dict) else {}
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            failures.append(f"canonical.nodes.{node_id} must be an object")
            continue
        if node.get("kind") not in UNIT_KINDS:
            failures.append(f"canonical.nodes.{node_id}.kind is invalid")
        require_string(node.get("name"), f"canonical.nodes.{node_id}.name", failures)
        if not node.get("candidate") and not node.get("evidence"):
            failures.append(f"canonical.nodes.{node_id} must retain source evidence")
    for interface_id, interface in interfaces.items():
        if interface.get("owner") not in nodes:
            failures.append(f"canonical.interfaces.{interface_id}.owner references a missing node")
        if not interface.get("evidence"):
            failures.append(f"canonical.interfaces.{interface_id} must retain source evidence")
    for relationship_id, relationship in relationships.items():
        if relationship.get("from") not in nodes or relationship.get("to") not in nodes:
            failures.append(f"canonical.relationships.{relationship_id} has a missing endpoint")
        if relationship.get("from") == relationship.get("to"):
            failures.append(f"canonical.relationships.{relationship_id} cannot be a self-relationship")
        require_string(relationship.get("purpose"), f"canonical.relationships.{relationship_id}.purpose", failures)
        require_string(relationship.get("technology"), f"canonical.relationships.{relationship_id}.technology", failures)
        if relationship.get("certainty") not in CERTAINTIES:
            failures.append(f"canonical.relationships.{relationship_id}.certainty is invalid")
        if not relationship.get("sourceFindings") or not relationship.get("evidence"):
            failures.append(f"canonical.relationships.{relationship_id} must retain findings and evidence")
        if relationship.get("destinationInterface") and relationship["destinationInterface"] not in interfaces:
            failures.append(f"canonical.relationships.{relationship_id}.destinationInterface is missing")
    for flow_id, flow in model.get("flows", {}).items():
        if flow.get("owner") not in nodes:
            failures.append(f"canonical.flows.{flow_id}.owner references a missing node")
        if flow.get("trigger") and flow["trigger"] not in interfaces:
            failures.append(f"canonical.flows.{flow_id}.trigger references a missing interface")
        for index, step in enumerate(flow.get("steps", [])):
            if step.get("at") and step["at"] not in nodes:
                failures.append(f"canonical.flows.{flow_id}.steps[{index}].at references a missing node")
            if step.get("relationship") and step["relationship"] not in relationships:
                failures.append(f"canonical.flows.{flow_id}.steps[{index}].relationship is missing")
    for boundary_id, boundary in model.get("systemBoundaries", {}).items():
        if not isinstance(boundary, dict):
            failures.append(f"canonical.systemBoundaries.{boundary_id} must be an object")
            continue
        if boundary.get("status") not in {"candidate", "confirmed", "rejected", "conflicting"}:
            failures.append(f"canonical.systemBoundaries.{boundary_id}.status is invalid")
        for member in boundary.get("members", []):
            if member not in nodes:
                failures.append(f"canonical.systemBoundaries.{boundary_id} references missing member {member}")
    return failures


def init_model(model_dir: Path, subject_name: str, sources: list[str]) -> None:
    if model_dir.exists() and any(model_dir.iterdir()):
        raise ModelError(f"model directory is not empty: {model_dir}")
    (model_dir / "scans").mkdir(parents=True, exist_ok=True)
    subject = {
        "schemaVersion": SCHEMA_VERSION,
        "subject": {
            "id": slug(subject_name),
            "name": subject_name,
            "description": f"Architecture discovery model for {subject_name}",
            "requestedSources": sources,
        },
    }
    decisions = {
        "schemaVersion": SCHEMA_VERSION,
        "identityOverrides": {},
        "targetOverrides": {},
        "systemBoundaries": {},
    }
    write_json(model_dir / "subject.json", subject)
    write_json(model_dir / "decisions.json", decisions)
    canonical = {
        "schemaVersion": SCHEMA_VERSION,
        "subject": subject["subject"],
        "sources": {},
        "nodes": {},
        "interfaces": {},
        "relationships": {},
        "flows": {},
        "systemBoundaries": {},
        "gaps": {},
        "conflicts": {},
    }
    write_json(model_dir / "canonical.json", canonical)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="initialize a model directory")
    init_parser.add_argument("model_dir", type=Path)
    init_parser.add_argument("--subject", required=True)
    init_parser.add_argument("--source", action="append", default=[])
    scan_parser = subparsers.add_parser("validate-scan", help="validate one repository scan")
    scan_parser.add_argument("scan", type=Path)
    compile_parser = subparsers.add_parser("compile", help="compile scans into canonical.json")
    compile_parser.add_argument("model_dir", type=Path)
    validate_parser = subparsers.add_parser("validate", help="validate an existing canonical.json")
    validate_parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            init_model(args.model_dir, args.subject, args.source)
            print(f"Initialized {args.model_dir}")
        elif args.command == "validate-scan":
            failures = validate_scan(load_json(args.scan), args.scan.name)
            if failures:
                raise ModelError("scan validation failed:\n- " + "\n- ".join(failures))
            print(f"Valid scan: {args.scan}")
        elif args.command == "compile":
            canonical = compile_model(args.model_dir)
            write_json(args.model_dir / "canonical.json", canonical)
            print(f"Compiled {args.model_dir / 'canonical.json'}")
        elif args.command == "validate":
            failures = validate_canonical(load_json(args.model_dir / "canonical.json"))
            if failures:
                raise ModelError("canonical validation failed:\n- " + "\n- ".join(failures))
            print(f"Valid canonical model: {args.model_dir / 'canonical.json'}")
    except ModelError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
