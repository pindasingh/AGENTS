import { Schema, actor, architecture, consumer, endpoint, evidence, external, flow, message, service, store, subscription, system, topic } from "./signal.js"

const fixture = (path: string, symbol: string | undefined, observation: string, certainty: "observed" | "inferred" | "unknown" = "observed") => evidence({
  repository: "dotnet-architecture/eShopOnContainers", revision: "dev (curated fixture)", path, ...(symbol ? { symbol } : {}), observation, certainty,
})
const boundaries = "evidence/storage-and-boundaries.md"
const trace = "evidence/execution-trace.md"

export const Browser = actor({ name: "Browser", evidence: [fixture(boundaries, undefined, "Browser application is a separate caller")] })
export const EShop = system({ name: "Microsoft eShopOnContainers", evidence: [fixture("README.md", undefined, "Curated checkout and asynchronous order-processing scope")] })
export const WebBff = service({ system: EShop, name: "Web BFF / API gateway", evidence: [fixture(boundaries, undefined, "Web BFF/API gateway is a separate ingress runtime")] })
export const BasketApi = service({ system: EShop, name: "Basket API" })
export const OrderingApi = service({ system: EShop, name: "Ordering API" })
export const CatalogApi = service({ system: EShop, name: "Catalog API" })
export const PaymentApi = service({ system: EShop, name: "Payment API" })
export const OrderingSignalRHub = service({ system: EShop, name: "Ordering SignalR Hub", evidence: [fixture(boundaries, undefined, "Downstream consumer of order-status integration events")] })
export const BasketRedis = store({ system: EShop, name: "Basket persistence", engine: "Redis", evidence: [fixture(boundaries, undefined, "Basket persistence is Redis")] })
export const OrderingSql = store({ system: EShop, name: "Ordering database", engine: "relational SQL", evidence: [fixture(boundaries, undefined, "Ordering owns a relational database")] })
export const CatalogSql = store({ system: EShop, name: "Catalog database", engine: "relational SQL", evidence: [fixture(boundaries, undefined, "Catalog owns a separate relational database")] })
export const RabbitMq = external({ name: "RabbitMQ event bus", evidence: [fixture(boundaries, undefined, "Development/test event-bus implementation; Azure Service Bus is an alternative")] })

const Checkout = Schema.Struct({ requestId: Schema.String, userId: Schema.String })
const Accepted = Schema.Struct({ status: Schema.Literal(202) })
const OrderEvent = Schema.Struct({ orderId: Schema.String })
export const WebCheckout = endpoint({ owner: WebBff, name: "Web checkout route", method: "POST", path: "/basket/checkout", request: Checkout, response: Accepted })
export const BasketCheckout = endpoint({ owner: BasketApi, name: "BasketController.CheckoutAsync", method: "POST", path: "/api/v1/basket/checkout", request: Checkout, response: Accepted, evidence: [fixture("evidence/BasketController.cs", "CheckoutAsync", "POST checkout reads basket, publishes checkout event, then returns Accepted")] })

export const UserCheckoutAcceptedIntegrationEvent = message({ name: "UserCheckoutAcceptedIntegrationEvent", schema: Checkout })
export const OrderStartedIntegrationEvent = message({ name: "OrderStartedIntegrationEvent", schema: OrderEvent })
export const OrderStatusChangedToSubmittedIntegrationEvent = message({ name: "OrderStatusChangedToSubmittedIntegrationEvent", schema: OrderEvent })
export const OrderStatusChangedToAwaitingValidationIntegrationEvent = message({ name: "OrderStatusChangedToAwaitingValidationIntegrationEvent", schema: OrderEvent })
export const OrderStatusChangedToStockConfirmedIntegrationEvent = message({ name: "OrderStatusChangedToStockConfirmedIntegrationEvent", schema: OrderEvent })
export const OrderStatusChangedToStockRejectedIntegrationEvent = message({ name: "OrderStatusChangedToStockRejectedIntegrationEvent", schema: OrderEvent, evidence: [fixture("README.md", undefined, "Catalog publishes a stock-rejected result; fixture does not expose its source declaration", "inferred")] })
export const OrderPaymentSuccededIntegrationEvent = message({ name: "OrderPaymentSuccededIntegrationEvent", schema: OrderEvent, evidence: [fixture(trace, undefined, "Exact published contract spelling in the execution facts")] })
export const OrderStatusChangedToPaidIntegrationEvent = message({ name: "Order paid status integration event (contract name not supplied)", schema: OrderEvent, evidence: [fixture("README.md", undefined, "Ordering publishes paid status; exact contract name is absent", "unknown")] })

export const IntegrationEvents = topic({ system: EShop, broker: RabbitMq, name: "Integration event bus", messages: [UserCheckoutAcceptedIntegrationEvent, OrderStartedIntegrationEvent, OrderStatusChangedToSubmittedIntegrationEvent, OrderStatusChangedToAwaitingValidationIntegrationEvent, OrderStatusChangedToStockConfirmedIntegrationEvent, OrderStatusChangedToStockRejectedIntegrationEvent, OrderPaymentSuccededIntegrationEvent, OrderStatusChangedToPaidIntegrationEvent] })
const sub = <A>(name: string, event: import("./signal.js").Message<A>) => subscription({ name, topic: IntegrationEvents, message: event })
export const OrderingCheckoutSubscription = sub("Ordering / checkout accepted", UserCheckoutAcceptedIntegrationEvent)
export const BasketOrderStartedSubscription = sub("Basket / order started", OrderStartedIntegrationEvent)
export const CatalogAwaitingValidationSubscription = sub("Catalog / awaiting validation", OrderStatusChangedToAwaitingValidationIntegrationEvent)
export const OrderingStockConfirmedSubscription = sub("Ordering / stock confirmed", OrderStatusChangedToStockConfirmedIntegrationEvent)
export const OrderingStockRejectedSubscription = sub("Ordering / stock rejected", OrderStatusChangedToStockRejectedIntegrationEvent)
export const PaymentStockConfirmedSubscription = sub("Payment / stock confirmed", OrderStatusChangedToStockConfirmedIntegrationEvent)
export const SignalRStockConfirmedSubscription = sub("SignalR / stock confirmed", OrderStatusChangedToStockConfirmedIntegrationEvent)
export const OrderingPaymentSucceededSubscription = sub("Ordering / payment succeeded", OrderPaymentSuccededIntegrationEvent)
export const OrderingCheckoutConsumer = consumer({ name: "UserCheckoutAcceptedIntegrationEventHandler", service: OrderingApi, subscription: OrderingCheckoutSubscription })
export const BasketOrderStartedConsumer = consumer({ name: "Basket order-started handler", service: BasketApi, subscription: BasketOrderStartedSubscription })
export const CatalogValidationConsumer = consumer({ name: "Catalog stock-validation handler", service: CatalogApi, subscription: CatalogAwaitingValidationSubscription })
export const OrderingStockConfirmedConsumer = consumer({ name: "Ordering stock-confirmed handler", service: OrderingApi, subscription: OrderingStockConfirmedSubscription })
export const OrderingStockRejectedConsumer = consumer({ name: "Ordering stock-rejected handler", service: OrderingApi, subscription: OrderingStockRejectedSubscription })
export const PaymentStockConfirmedConsumer = consumer({ name: "Payment stock-confirmed handler", service: PaymentApi, subscription: PaymentStockConfirmedSubscription })
export const SignalRStockConfirmedConsumer = consumer({ name: "Ordering SignalR stock-confirmed handler", service: OrderingSignalRHub, subscription: SignalRStockConfirmedSubscription })
export const OrderingPaymentSucceededConsumer = consumer({ name: "Ordering payment-succeeded handler", service: OrderingApi, subscription: OrderingPaymentSucceededSubscription })

export const CheckoutAcceptance = flow("HTTP checkout acceptance — HTTP 202 occurs before order creation", ({ step }) => {
  const web = step.request({ from: Browser, to: WebCheckout, input: { requestId: "x-requestid", userId: "customer" } })
  const checkout = step.request({ from: WebBff, to: BasketCheckout, input: { requestId: "x-requestid", userId: "customer" } })
  const basket = step.read({ by: BasketApi, from: BasketRedis, forStep: checkout, schema: Checkout, operation: "GetBasketAsync(customer identity)" })
  step.publish({ by: BasketApi, value: basket, message: UserCheckoutAcceptedIntegrationEvent, to: IntegrationEvents, operation: "Publish UserCheckoutAcceptedIntegrationEvent" })
  step.respond({ value: checkout, via: BasketCheckout, operation: "HTTP 202 Accepted — exact acceptance point" })
  step.respond({ value: web, via: WebCheckout, operation: "HTTP 202 Accepted to browser" })
})

export const CreateOrder = flow("Asynchronous order creation", ({ step }) => {
  const start = step.continue({ message: UserCheckoutAcceptedIntegrationEvent, from: IntegrationEvents })
  const delivered = step.deliver({ value: start, to: OrderingCheckoutSubscription })
  const consumed = step.consume({ value: delivered, by: OrderingCheckoutConsumer, operation: "Handle UserCheckoutAcceptedIntegrationEvent; dispatch idempotent IdentifiedCommand<CreateOrderCommand, bool> using RequestId" })
  const order = step.derive({ by: OrderingApi, value: consumed, schema: OrderEvent, operation: "CreateOrderCommandHandler creates Order" })
  step.write({ by: OrderingApi, value: order, to: OrderingSql, operation: "SaveEntitiesAsync: persist order and integration-event records in transaction" })
  step.publish({ by: OrderingApi, value: order, message: OrderStartedIntegrationEvent, to: IntegrationEvents })
  step.publish({ by: OrderingApi, value: order, message: OrderStatusChangedToSubmittedIntegrationEvent, to: IntegrationEvents })
  step.publish({ by: OrderingApi, value: order, message: OrderStatusChangedToAwaitingValidationIntegrationEvent, to: IntegrationEvents, operation: "Publish awaiting-validation status after transaction" })
}, { continuesFrom: [CheckoutAcceptance] })

export const ClearBasket = flow("Clear checked-out basket", ({ step }) => {
  const event = step.continue({ message: OrderStartedIntegrationEvent, from: IntegrationEvents }); const delivered = step.deliver({ value: event, to: BasketOrderStartedSubscription }); const consumed = step.consume({ value: delivered, by: BasketOrderStartedConsumer }); step.delete({ by: BasketOrderStartedConsumer, value: consumed, from: BasketRedis, operation: "Delete checked-out basket" })
}, { continuesFrom: [CreateOrder] })
export const ConfirmStock = flow("Catalog confirms stock", ({ step }) => {
  const event = step.continue({ message: OrderStatusChangedToAwaitingValidationIntegrationEvent, from: IntegrationEvents }); const delivered = step.deliver({ value: event, to: CatalogAwaitingValidationSubscription }); const consumed = step.consume({ value: delivered, by: CatalogValidationConsumer }); step.write({ by: CatalogValidationConsumer, value: consumed, to: CatalogSql, operation: "Validate and decrement stock" }); step.publish({ by: CatalogValidationConsumer, value: consumed, message: OrderStatusChangedToStockConfirmedIntegrationEvent, to: IntegrationEvents })
}, { continuesFrom: [CreateOrder] })
export const RejectStock = flow("Stock rejection — terminal rejected branch", ({ step }) => {
  const event = step.continue({ message: OrderStatusChangedToAwaitingValidationIntegrationEvent, from: IntegrationEvents }); const delivered = step.deliver({ value: event, to: CatalogAwaitingValidationSubscription }); const consumed = step.consume({ value: delivered, by: CatalogValidationConsumer }); step.write({ by: CatalogValidationConsumer, value: consumed, to: CatalogSql, operation: "Validate stock; insufficient stock" }); step.publish({ by: CatalogValidationConsumer, value: consumed, message: OrderStatusChangedToStockRejectedIntegrationEvent, to: IntegrationEvents }); const result = step.continue({ message: OrderStatusChangedToStockRejectedIntegrationEvent, from: IntegrationEvents }); const routed = step.deliver({ value: result, to: OrderingStockRejectedSubscription }); const handled = step.consume({ value: routed, by: OrderingStockRejectedConsumer }); step.write({ by: OrderingStockRejectedConsumer, value: handled, to: OrderingSql, operation: "Cancel order" })
}, { continuesFrom: [CreateOrder] })
export const NotifyAndPay = flow("Stock-confirmed fan-out: notification and payment", ({ step }) => {
  const event = step.continue({ message: OrderStatusChangedToStockConfirmedIntegrationEvent, from: IntegrationEvents }); const orderDelivery = step.deliver({ value: event, to: OrderingStockConfirmedSubscription }); const orderHandled = step.consume({ value: orderDelivery, by: OrderingStockConfirmedConsumer }); step.write({ by: OrderingStockConfirmedConsumer, value: orderHandled, to: OrderingSql, operation: "Change order state to stock confirmed" }); const notifyDelivery = step.deliver({ value: event, to: SignalRStockConfirmedSubscription }); step.consume({ value: notifyDelivery, by: SignalRStockConfirmedConsumer, operation: "Notify connected clients of stock-confirmed status" }); const payDelivery = step.deliver({ value: event, to: PaymentStockConfirmedSubscription }); const payment = step.consume({ value: payDelivery, by: PaymentStockConfirmedConsumer, operation: "Process payment (sample successful flow)" }); step.publish({ by: PaymentStockConfirmedConsumer, value: payment, message: OrderPaymentSuccededIntegrationEvent, to: IntegrationEvents })
}, { continuesFrom: [ConfirmStock] })
export const CompleteOrder = flow("Successful completion", ({ step }) => {
  const event = step.continue({ message: OrderPaymentSuccededIntegrationEvent, from: IntegrationEvents }); const delivered = step.deliver({ value: event, to: OrderingPaymentSucceededSubscription }); const consumed = step.consume({ value: delivered, by: OrderingPaymentSucceededConsumer }); step.write({ by: OrderingPaymentSucceededConsumer, value: consumed, to: OrderingSql, operation: "Mark order paid" }); step.publish({ by: OrderingPaymentSucceededConsumer, value: consumed, message: OrderStatusChangedToPaidIntegrationEvent, to: IntegrationEvents, operation: "Publish paid status (exact contract name unavailable in fixture)" })
}, { continuesFrom: [NotifyAndPay] })
export const PaymentFailureUnresolved = flow("Payment failure — required variant, behavior unresolved by supplied evidence", ({ step }) => {
  const event = step.continue({ message: OrderStatusChangedToStockConfirmedIntegrationEvent, from: IntegrationEvents, operation: "Payment failure branch begins after stock confirmation; no failure contract or resulting state is supplied" }); const delivered = step.deliver({ value: event, to: PaymentStockConfirmedSubscription }); step.consume({ value: delivered, by: PaymentStockConfirmedConsumer, operation: "Payment outcome: failure (terminal behavior unknown; intentionally not invented)" })
}, { continuesFrom: [ConfirmStock], evidence: [fixture("README.md", undefined, "Requires payment-failure path, but supplies no failure contract or terminal behavior", "unknown")] })

export default architecture({ Browser, EShop, WebBff, BasketApi, OrderingApi, CatalogApi, PaymentApi, OrderingSignalRHub, BasketRedis, OrderingSql, CatalogSql, RabbitMq, WebCheckout, BasketCheckout, UserCheckoutAcceptedIntegrationEvent, OrderStartedIntegrationEvent, OrderStatusChangedToSubmittedIntegrationEvent, OrderStatusChangedToAwaitingValidationIntegrationEvent, OrderStatusChangedToStockConfirmedIntegrationEvent, OrderStatusChangedToStockRejectedIntegrationEvent, OrderPaymentSuccededIntegrationEvent, OrderStatusChangedToPaidIntegrationEvent, IntegrationEvents, OrderingCheckoutSubscription, BasketOrderStartedSubscription, CatalogAwaitingValidationSubscription, OrderingStockConfirmedSubscription, OrderingStockRejectedSubscription, PaymentStockConfirmedSubscription, SignalRStockConfirmedSubscription, OrderingPaymentSucceededSubscription, OrderingCheckoutConsumer, BasketOrderStartedConsumer, CatalogValidationConsumer, OrderingStockConfirmedConsumer, OrderingStockRejectedConsumer, PaymentStockConfirmedConsumer, SignalRStockConfirmedConsumer, OrderingPaymentSucceededConsumer, CheckoutAcceptance, CreateOrder, ClearBasket, ConfirmStock, RejectStock, NotifyAndPay, CompleteOrder, PaymentFailureUnresolved })
