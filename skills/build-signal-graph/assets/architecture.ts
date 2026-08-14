import {
  Schema, actor, architecture, consumer, endpoint, external, flow,
  message, service, store, subscription, system, topic,
} from "./signal.js"

export const Customer = actor({ name: "Customer" })
export const Ordering = system({ name: "Ordering" })
export const OrdersApi = service({ system: Ordering, name: "Orders API", technology: ["TypeScript", "Effect"] })
export const ShippingWorker = service({ system: Ordering, name: "Shipping Worker", technology: ["TypeScript", "Effect"] })
export const Orders = store({ system: Ordering, name: "Orders", engine: "PostgreSQL" })
export const PaymentProvider = external({ name: "Payment Provider" })

export const SubmitOrder = endpoint({
  owner: OrdersApi,
  name: "Submit order",
  method: "POST",
  path: "/orders",
  request: Schema.Struct({ productId: Schema.String, quantity: Schema.Number }),
  response: Schema.Struct({ orderId: Schema.String, status: Schema.Literal("accepted") }),
})

export const ChargePayment = endpoint({
  owner: PaymentProvider,
  name: "Charge payment",
  method: "POST",
  path: "/payments",
  request: Schema.Struct({ orderId: Schema.String }),
  response: Schema.Struct({ paymentId: Schema.String }),
})

export const OrderCreated = message({
  name: "order.created",
  schema: Schema.Struct({ orderId: Schema.String }),
})
export const OrderEvents = topic({ system: Ordering, name: "order-events", messages: [OrderCreated] })
export const ShippingOrders = subscription({ name: "shipping-orders", topic: OrderEvents, message: OrderCreated })
export const Shipping = consumer({ name: "shipping", service: ShippingWorker, subscription: ShippingOrders })

export const SubmitOrderFlow = flow("submit-order", ({ step }) => {
  const request = step.request(Customer, SubmitOrder, { productId: "example", quantity: 1 })
  const persisted = step.write(request, Orders)
  step.respond(persisted, SubmitOrder)
  const published = step.publish({ ...persisted, value: { orderId: "derived" } }, OrderCreated, OrderEvents)
  const delivered = step.deliver(published, ShippingOrders)
  const consumed = step.consume(delivered, Shipping)
  step.request(Shipping, ChargePayment, { orderId: "derived" })
})

export default architecture({
  Customer, Ordering, OrdersApi, ShippingWorker, Orders, PaymentProvider,
  SubmitOrder, ChargePayment, OrderCreated, OrderEvents, ShippingOrders, Shipping,
  SubmitOrderFlow,
})
