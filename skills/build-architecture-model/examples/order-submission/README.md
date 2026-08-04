# Inspectable sharded model example

This complete two-repository example models the **Submit order** operation from an Orders Web caller through an Orders API handler and Orders store, then back to the caller.

Start with these files:

1. [`.architecture-model/index.json`](.architecture-model/index.json) — compact hierarchy, artifact links, and hashes; no copied architecture records.
2. [Domain](.architecture-model/domains/domain.ordering.json) — links the domain to its sources, components, and operation.
3. [Web component](.architecture-model/components/component.client.order-form.json) and [API component](.architecture-model/components/component.api.submit-handler.json) — responsibilities, runtime owners, operation links, and evidence.
4. [Operation](.architecture-model/operations/operation.submit-order/operation.json) — owning components, trigger, and path variants.
5. [Canonical successful path](.architecture-model/operations/operation.submit-order/paths/path.submit-order.success.json) — authoritative numbered execution.
6. [Numbered review](.architecture-model/projections/operation.submit-order/path.submit-order.success/numbered-sequence.md) and [ASCII review](.architecture-model/projections/operation.submit-order/path.submit-order.success/sequence-diagram.txt) — generated human views.
7. [Orders Web scan](.architecture-model/sources/source.orders-web/scan.json) and [Orders API scan](.architecture-model/sources/source.orders-api/scan.json) — repository-local evidence and reciprocal repository discovery.

Validate it from the skill directory:

```bash
python scripts/architecture_model.py validate examples/order-submission/.architecture-model
```

Regenerating the projections and index is deterministic:

```bash
python scripts/architecture_model.py format examples/order-submission/.architecture-model
python scripts/architecture_model.py render examples/order-submission/.architecture-model
python scripts/architecture_model.py index examples/order-submission/.architecture-model
```
