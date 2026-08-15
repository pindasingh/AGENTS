import { Schema, actor, architecture, consumer, endpoint, external, flow, message, service, store, subscription, system, topic } from "./signal.js"

export const Customer = actor({ name: "Customer" })
export const Ordering = system({ name: "Ordering" })
export const WebBff = service({ system: Ordering, name: "Web BFF", technology: ["TypeScript"] })
export const OrdersApi = service({ system: Ordering, name: "Orders API", technology: ["TypeScript"] })
export const ShippingWorker = service({ system: Ordering, name: "Shipping Worker", technology: ["TypeScript"] })
export const Orders = store({ system: Ordering, name: "Orders", engine: "PostgreSQL" })
export const OrdersCache = store({ system: Ordering, name: "Orders cache", engine: "Redis" })
export const EventBus = external({ name: "Message bus" })
export const PaymentProvider = external({ name: "Payment Provider" })
const OrderRequest = Schema.Struct({ productId: Schema.String, quantity: Schema.Number })
const OrderResult = Schema.Struct({ orderId: Schema.String, status: Schema.Literal("accepted") })
const OrderEvent = Schema.Struct({ orderId: Schema.String })

export const SubmitOrder = endpoint({ owner: OrdersApi, name: "Submit order", method: "POST", path: "/orders", request: OrderRequest, response: OrderResult })
export const BffSubmitOrder = endpoint({ owner: WebBff, name: "Web submit order", method: "POST", path: "/orders", request: OrderRequest, response: OrderResult })
export const ChargePayment = endpoint({ owner: PaymentProvider, name: "Charge payment", method: "POST", path: "/payments", request: OrderEvent, response: Schema.Struct({ paymentId: Schema.String }) })
export const OrderCreated = message({ name: "order.created", schema: OrderEvent })
export const OrderEvents = topic({ system: Ordering, broker: EventBus, name: "order-events", messages: [OrderCreated] })
export const ShippingOrders = subscription({ name: "shipping-orders", topic: OrderEvents, message: OrderCreated })
export const Shipping = consumer({ name: "shipping", service: ShippingWorker, subscription: ShippingOrders })

export const SubmitOrderFlow = flow("submit-order", ({ step }) => {
  const ingress = step.request({ from: Customer, to: BffSubmitOrder, input: { productId: "example", quantity: 1 } })
  const request = step.request({ from: WebBff, to: SubmitOrder, input: { productId: "example", quantity: 1 } })
  step.read({ by: OrdersApi, from: OrdersCache, forStep: request, schema: OrderResult, operation: "GET cached order" })
  const persisted = step.write({ by: OrdersApi, value: request, to: Orders, operation: "INSERT order" })
  step.respond({ value: request, via: SubmitOrder })
  step.respond({ value: ingress, via: BffSubmitOrder })
  const event = step.derive({ by: OrdersApi, value: persisted, schema: OrderEvent, operation: "create order event" })
  step.publish({ by: OrdersApi, value: event, message: OrderCreated, to: OrderEvents })
})

export const ShippingFlow = flow("ship-created-order", ({ step }) => {
  const event = step.continue({ message: OrderCreated, from: OrderEvents })
  const delivered = step.deliver({ value: event, to: ShippingOrders })
  const consumed = step.consume({ value: delivered, by: Shipping })
  step.request({ from: Shipping, to: ChargePayment, input: consumed.value })
}, { continuesFrom: [SubmitOrderFlow] })

export default architecture({ Customer, Ordering, WebBff, OrdersApi, ShippingWorker, Orders, OrdersCache, EventBus, PaymentProvider, SubmitOrder, BffSubmitOrder, ChargePayment, OrderCreated, OrderEvents, ShippingOrders, Shipping, SubmitOrderFlow, ShippingFlow })
