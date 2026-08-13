# TypeScript Signal DSL

The DSL makes architecture readable as code and makes invalid relationships type errors. Its vocabulary is deliberately architectural rather than a generic graph schema.

## Declarations

```ts
const Ordering = system({ name: "Ordering" })
const OrdersApi = service({ system: Ordering, name: "Orders API" })
const Orders = store({ system: Ordering, name: "Orders", engine: "PostgreSQL" })
```

Use direct object references for ownership and relationships. Renaming a declaration is then a normal TypeScript refactor rather than an ID migration.

## HTTP

```ts
const SubmitOrder = endpoint({
  owner: OrdersApi,
  name: "Submit order",
  method: "POST",
  path: "/orders",
  request: Schema.Struct({ productId: Schema.String, quantity: Schema.Number }),
  response: Schema.Struct({ orderId: Schema.String }),
})
```

An endpoint describes both sides of one request/response contract. A flow calls `step.request` and later `step.respond`; no `mode` property exists.

## Messaging

```ts
const OrderCreated = message({
  name: "order.created",
  schema: Schema.Struct({ orderId: Schema.String }),
})
const Events = topic({ system: Ordering, name: "order-events", messages: [OrderCreated] })
const ShippingOrders = subscription({ name: "shipping-orders", topic: Events, message: OrderCreated })
const Shipping = consumer({ name: "shipping", service: ShippingWorker, subscription: ShippingOrders })
```

Keep publication, delivery, and consumption separate. The distinction represents fan-out and subscription topology without reducing the whole system to messaging.

## Flows

```ts
const SubmitOrderFlow = flow("submit-order", ({ step }) => {
  const request = step.request(Customer, SubmitOrder, input)
  const persisted = step.write(request, Orders)
  step.respond(persisted, SubmitOrder)
  const published = step.publish(orderCreated, OrderCreated, Events)
  const delivered = step.deliver(published, ShippingOrders)
  step.consume(delivered, Shipping)
})
```

A flow is an ordered architectural scenario, not application implementation. Include boundary crossings and durable effects; omit ordinary calculations. Use separate flows when branching would hide materially different outcomes.

## Evidence

```ts
const source = evidence({
  repository: "orders-api",
  revision: "4f12c9a",
  path: "src/http/orders.ts",
  symbol: "submitOrder",
  observation: "Registers POST /orders and calls the order application service",
  certainty: "observed",
})
```

Attach evidence where it supports a declaration. Do not create parallel evidence ledgers or synthetic stable IDs.

## Extending the DSL

Prefer a named architectural constructor or step over metadata flags. Add a new concept only when it has distinct ownership, contract, or flow semantics that TypeScript can enforce. Do not add generic `node`, `edge`, `kind`, or `mode` escape hatches merely to make an awkward model compile.
