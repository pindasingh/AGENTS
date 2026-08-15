# TypeScript Signal DSL

The DSL makes architecture readable as code and invalid relationships type errors. Its vocabulary is architectural rather than a generic graph schema. Object identity is authoritative: one declaration becomes one architecture box wherever it participates.

## Components and ownership

```ts
const Ordering = system({ name: "Ordering" })
const OrdersApi = service({ system: Ordering, name: "Orders API" })
const Orders = store({ system: Ordering, name: "Orders", engine: "PostgreSQL" })
const Broker = external({ name: "RabbitMQ" })
```

Use direct references. Do not reproduce names as IDs.

## HTTP contracts

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

The endpoint is a contract attached to its owner. In an architecture projection, `step.request` creates a labelled arrow to that owner rather than another endpoint box:

```ts
const submitted = step.request({
  from: WebBff,
  to: SubmitOrder,
  input,
})
```

## Explicit persistence interactions

The executor and operation are mandatory because data lineage alone does not prove which component performs an effect:

```ts
const cached = step.read({
  by: OrdersApi,
  from: OrdersCache,
  forStep: submitted,
  schema: Order,
  operation: "GET cached order",
})

const persisted = step.write({
  by: OrdersApi,
  value: submitted,
  to: Orders,
  operation: "INSERT order",
})

step.delete({
  by: BasketApi,
  value: checkout,
  from: BasketCache,
  operation: "EVICT checked-out basket",
})
```

Keep `GET`, `SET`, `EVICT`, `INSERT`, `UPDATE`, and `DELETE` as separate steps. Do not combine them into one slash-separated operation.

## Messaging

```ts
const OrderCreated = message({ name: "order.created", schema: OrderEvent })
const Events = topic({ system: Ordering, broker: Broker, name: "order-events", messages: [OrderCreated] })
const ShippingOrders = subscription({ name: "shipping-orders", topic: Events, message: OrderCreated })
const Shipping = consumer({ name: "shipping", service: ShippingWorker, subscription: ShippingOrders })
```

Publisher identity is explicit:

```ts
step.publish({
  by: OrdersApi,
  value: orderEvent,
  message: OrderCreated,
  to: Events,
  operation: "publish order.created",
})
```

A separately modeled continuation starts from its message/topic and retains a typed causal link to its predecessor flow:

```ts
const ProcessCreatedOrder = flow("process-created-order", ({ step }) => {
  const event = step.continue({ message: OrderCreated, from: Events })
  const delivered = step.deliver({ value: event, to: ShippingOrders })
  step.consume({ value: delivered, by: Shipping })
}, { continuesFrom: [SubmitOrder] })
```

Publication, delivery, and consumption remain separate model facts. A renderer may project the broker/topic and consumer service as the visible boxes while retaining message and subscription identities as interaction provenance.

## Contract transformation

Use `derive` only when an evidenced boundary operation changes one architectural contract into another:

```ts
const event = step.derive({
  by: OrdersApi,
  value: persisted,
  schema: OrderCreated.schema,
  operation: "create order-created event",
})
```

Ordinary implementation calculations do not belong in the architecture model.

## Path variants

A flow is one ordered architectural scenario or scenario segment. Use separate flows for materially different callers and outcomes. Connect asynchronous segments through `continuesFrom` so tools can construct complete root-to-leaf paths:

```text
Web acceptance ─┐
                ├─▶ Order creation ─▶ Stock confirmed ─┬─▶ Payment succeeded
Mobile acceptance┘                                     └─▶ Payment failed
                                  └─▶ Stock rejected
```

This lets an interactive projection select `POST /orders` and highlight everything that path touches across HTTP, persistence, transport, workers, downstream APIs, and terminal effects.

## Evidence

Attach evidence to declarations and disputed interactions. Step methods accept `evidence` alongside `operation`.

```ts
const source = evidence({
  repository: "orders-api",
  revision: "4f12c9a",
  path: "src/http/orders.ts",
  symbol: "submitOrder",
  observation: "Registers POST /orders and writes the order",
  certainty: "observed",
})
```

Do not create a parallel evidence ledger or synthetic stable IDs.

## Extending the DSL

Prefer a named architectural constructor or step over metadata flags. Add a concept only when it has distinct ownership, contract, or flow semantics that TypeScript can enforce. Do not add generic nodes or edges merely to make an awkward model compile.
