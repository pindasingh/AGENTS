# Submit order â€” successful path

- Path ID: `path.submit-order.success`
- Operation ID: `operation.submit-order`
- Path kind: success
- Trigger interface IDs: interface.api.submit-order
- Evidenced callers: runtime.client
- Participant IDs: runtime.client | runtime.api | component.api.submit-handler | store.orders
- Outcome: 2.1 — Caller receives OrderResponse
- Coverage: complete

## Numbered execution

1. **Request enters the Orders API**
  1.1. **Sends POST /api/orders**
     - Execution: `runtime.client -> runtime.api`
     - kind=entry; boundary=runtime; input=OrderRequest; output=Accepted request; interface=interface.api.submit-order; continuation=continue; certainty=corroborated
     - Evidence: source.orders-web:src/api/orders.ts — Calls POST /api/orders with OrderRequest v1
  1.2. **Validates the submitted order**
     - Execution: `component.api.submit-handler -> component.api.submit-handler`
     - kind=local-operation; boundary=in-process; input=OrderRequest; output=Validated order; continuation=continue; certainty=observed
     - Evidence: source.orders-api:src/Orders.cs — Fixture evidence
  1.3. **Stores the accepted order**
     - Execution: `component.api.submit-handler -> store.orders`
     - kind=data-write; boundary=data-store; input=Validated order; output=Persisted order; relationship=relationship.api.write-orders; continuation=continue; certainty=observed
     - Evidence: source.orders-api:src/Orders.cs — Fixture evidence
2. **Response returns**
  2.1. **Returns OrderResponse to the caller**
     - Execution: `runtime.api -> runtime.client`
     - kind=return; boundary=runtime; input=Persisted order; output=OrderResponse; interface=interface.api.submit-order; continuation=return; certainty=corroborated
     - Evidence: source.orders-api:src/Orders.cs — Fixture evidence

## Unresolved points and omissions

- Gap IDs: none
- Known omissions: none
