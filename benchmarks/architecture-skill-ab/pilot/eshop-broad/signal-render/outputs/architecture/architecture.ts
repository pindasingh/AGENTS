import { Schema, actor, architecture, consumer, endpoint, evidence, external, flow, message, service, store, subscription, system, topic } from "./signal.js"
import type { Steps } from "./signal.js"

const repo = "dotnet-architecture/eShopOnContainers"
const revision = "dev"
const ev = (path: string, observation: string, symbol?: string) => [evidence({ repository: repo, revision, path, ...(symbol ? { symbol } : {}), observation, certainty: "observed" })]
const boundaries = "evidence/storage-and-boundaries.md"
const trace = "evidence/execution-trace.md"
const fixture = "README.md"

export const BrowserCustomer = actor({ name: "Browser customer", evidence: ev(boundaries, "Browser application is a separate caller") })
export const MobileCustomer = actor({ name: "Mobile customer", evidence: ev(boundaries, "Mobile application is a separate caller") })
export const EShop = system({ name: "eShopOnContainers", description: "Owned application boundary represented by the selected checkout fixture", evidence: ev(fixture, "Fixture scopes the public checkout and order process") })
export const WebBff = service({ system: EShop, name: "Web BFF / API gateway", evidence: ev(boundaries, "Web gateway is a separate ingress runtime") })
export const MobileBff = service({ system: EShop, name: "Mobile BFF / API gateway", evidence: ev(boundaries, "Mobile gateway is a separate ingress runtime") })
export const BasketApi = service({ system: EShop, name: "Basket API", evidence: ev(boundaries, "Basket is a separate microservice") })
export const OrderingApi = service({ system: EShop, name: "Ordering API", evidence: ev(boundaries, "Ordering is a separate microservice") })
export const CatalogApi = service({ system: EShop, name: "Catalog API", evidence: ev(boundaries, "Catalog is a separate microservice") })
export const PaymentApi = service({ system: EShop, name: "Payment API", evidence: ev(boundaries, "Payment is a separate microservice") })
export const OrderingSignalRHub = service({ system: EShop, name: "Ordering SignalR Hub", description: "Downstream order-status notification consumer", evidence: ev(boundaries, "Ordering SignalR Hub consumes order-status integration events") })
export const BasketRedis = store({ system: EShop, name: "Basket data", engine: "Redis", evidence: ev(boundaries, "Basket persistence is Redis") })
export const OrderingSql = store({ system: EShop, name: "Ordering data", engine: "Relational SQL", evidence: ev(boundaries, "Ordering owns a relational database") })
export const CatalogSql = store({ system: EShop, name: "Catalog data", engine: "Relational SQL", evidence: ev(boundaries, "Catalog owns a separate relational database") })
export const EventBus = external({ name: "Event bus (RabbitMQ / Azure Service Bus)", description: "RabbitMQ in development/test; Azure Service Bus is a replaceable alternative", evidence: ev(boundaries, "Published event-bus infrastructure choices") })

const Checkout = Schema.Struct({ requestId: Schema.String, userId: Schema.String })
const Accepted = Schema.Struct({ status: Schema.Literal(202) })
const OrderEvent = Schema.Struct({ requestId: Schema.String, orderId: Schema.String })
const StockEvent = Schema.Struct({ requestId: Schema.String, orderId: Schema.String })
const PaymentEvent = Schema.Struct({ requestId: Schema.String, orderId: Schema.String })
const StatusEvent = Schema.Struct({ requestId: Schema.String, orderId: Schema.String })

export const WebCheckout = endpoint({ owner: WebBff, name: "Web checkout ingress", method: "POST", path: "/checkout", request: Checkout, response: Accepted, evidence: ev(fixture, "Web client enters through its BFF over HTTP/REST") })
export const MobileCheckout = endpoint({ owner: MobileBff, name: "Mobile checkout ingress", method: "POST", path: "/checkout", request: Checkout, response: Accepted, evidence: ev(fixture, "Mobile client enters through its BFF over HTTP/REST") })
export const BasketCheckout = endpoint({ owner: BasketApi, name: "Basket checkout", method: "POST", path: "/api/v1/basket/checkout", request: Checkout, response: Accepted, evidence: ev("evidence/BasketController.cs", "Checkout endpoint reads Basket, publishes acceptance event, and returns Accepted", "CheckoutAsync") })

export const CheckoutAccepted = message({ name: "UserCheckoutAcceptedIntegrationEvent", schema: Checkout, evidence: ev("evidence/BasketController.cs", "Basket publishes checkout data and request ID", "CheckoutAsync") })
export const OrderStarted = message({ name: "OrderStartedIntegrationEvent", schema: OrderEvent, evidence: ev(trace, "Ordering publishes OrderStarted after commit") })
export const AwaitingValidation = message({ name: "OrderStatusChangedToAwaitingValidationIntegrationEvent", schema: OrderEvent, evidence: ev(fixture, "Catalog consumes awaiting-validation status") })
export const StockConfirmed = message({ name: "OrderStockConfirmedIntegrationEvent", schema: StockEvent, evidence: ev(fixture, "Catalog publishes stock-confirmed outcome") })
export const StockRejected = message({ name: "OrderStockRejectedIntegrationEvent", schema: StockEvent, evidence: ev(fixture, "Catalog publishes stock-rejected outcome") })
export const StatusStockConfirmed = message({ name: "OrderStatusChangedToStockConfirmedIntegrationEvent", schema: StockEvent, evidence: ev(trace, "Payment and Ordering SignalR Hub handle stock-confirmed status") })
export const PaymentSucceeded = message({ name: "OrderPaymentSuccededIntegrationEvent", schema: PaymentEvent, evidence: ev(trace, "Payment publishes payment-succeeded event") })
export const PaymentFailed = message({ name: "OrderPaymentFailedIntegrationEvent", schema: PaymentEvent, evidence: ev(fixture, "Required payment-failure path terminates in cancellation") })
export const PaidStatus = message({ name: "OrderStatusChangedToPaidIntegrationEvent", schema: StatusEvent, evidence: ev(fixture, "Paid status is published and propagated") })
export const CancelledStatus = message({ name: "OrderStatusChangedToCancelledIntegrationEvent", schema: StatusEvent, evidence: ev(fixture, "Rejected/payment-failed outcomes persist and propagate cancellation") })
export const IntegrationEvents = topic({ system: EShop, broker: EventBus, name: "Integration events", messages: [CheckoutAccepted, OrderStarted, AwaitingValidation, StockConfirmed, StockRejected, StatusStockConfirmed, PaymentSucceeded, PaymentFailed, PaidStatus, CancelledStatus], evidence: ev(fixture, "Services coordinate through integration events over a message bus") })

const sub = <A>(name: string, msg: import("./signal.js").Message<A>) => subscription({ name, topic: IntegrationEvents, message: msg })
export const OrderingCheckoutSub = sub("Ordering checkout", CheckoutAccepted)
export const BasketOrderStartedSub = sub("Basket order started", OrderStarted)
export const CatalogValidationSub = sub("Catalog awaiting validation", AwaitingValidation)
export const OrderingStockConfirmedSub = sub("Ordering stock confirmed", StockConfirmed)
export const OrderingStockRejectedSub = sub("Ordering stock rejected", StockRejected)
export const PaymentStockConfirmedSub = sub("Payment stock confirmed", StatusStockConfirmed)
export const OrderingPaymentSucceededSub = sub("Ordering payment succeeded", PaymentSucceeded)
export const OrderingPaymentFailedSub = sub("Ordering payment failed", PaymentFailed)
export const HubStockConfirmedSub = sub("Hub stock confirmed", StatusStockConfirmed)
export const HubPaidSub = sub("Hub paid", PaidStatus)
export const HubCancelledSub = sub("Hub cancelled", CancelledStatus)
export const OrderingCheckoutConsumer = consumer({ name: "Ordering checkout handler", service: OrderingApi, subscription: OrderingCheckoutSub })
export const BasketOrderStartedConsumer = consumer({ name: "Basket order-started handler", service: BasketApi, subscription: BasketOrderStartedSub })
export const CatalogValidationConsumer = consumer({ name: "Catalog validation handler", service: CatalogApi, subscription: CatalogValidationSub })
export const OrderingStockConfirmedConsumer = consumer({ name: "Ordering stock-confirmed handler", service: OrderingApi, subscription: OrderingStockConfirmedSub })
export const OrderingStockRejectedConsumer = consumer({ name: "Ordering stock-rejected handler", service: OrderingApi, subscription: OrderingStockRejectedSub })
export const PaymentStockConfirmedConsumer = consumer({ name: "Payment stock-confirmed handler", service: PaymentApi, subscription: PaymentStockConfirmedSub })
export const OrderingPaymentSucceededConsumer = consumer({ name: "Ordering payment-succeeded handler", service: OrderingApi, subscription: OrderingPaymentSucceededSub })
export const OrderingPaymentFailedConsumer = consumer({ name: "Ordering payment-failed handler", service: OrderingApi, subscription: OrderingPaymentFailedSub })
export const HubStockConfirmedConsumer = consumer({ name: "Hub stock-confirmed handler", service: OrderingSignalRHub, subscription: HubStockConfirmedSub })
export const HubPaidConsumer = consumer({ name: "Hub paid handler", service: OrderingSignalRHub, subscription: HubPaidSub })
export const HubCancelledConsumer = consumer({ name: "Hub cancelled handler", service: OrderingSignalRHub, subscription: HubCancelledSub })

const checkoutInput = { requestId: "correlation-id", userId: "customer-id" }
const acceptance = (name: string, caller: typeof BrowserCustomer, ingress: typeof WebCheckout, gateway: typeof WebBff) => flow(name, ({ step }) => {
  const entry = step.request({ from: caller, to: ingress, input: checkoutInput })
  const checkout = step.request({ from: gateway, to: BasketCheckout, input: checkoutInput })
  step.read({ by: BasketApi, from: BasketRedis, forStep: checkout, schema: Checkout, operation: "GET customer basket", evidence: ev("evidence/BasketController.cs", "Checkout reads basket from repository", "CheckoutAsync") })
  const acceptedEvent = step.derive({ by: BasketApi, value: checkout, schema: Checkout, operation: "create checkout-accepted event" })
  step.publish({ by: BasketApi, value: acceptedEvent, message: CheckoutAccepted, to: IntegrationEvents, operation: "publish checkout accepted", evidence: ev("evidence/BasketController.cs", "Publish occurs before Accepted response", "CheckoutAsync") })
  step.respond({ value: checkout, via: BasketCheckout, operation: "HTTP 202 Accepted" })
  step.respond({ value: entry, via: ingress, operation: "HTTP 202 Accepted" })
})
export const WebCheckoutAcceptance = acceptance("web checkout acceptance", BrowserCustomer, WebCheckout, WebBff)
export const MobileCheckoutAcceptance = acceptance("mobile checkout acceptance", MobileCustomer, MobileCheckout, MobileBff)
const acceptedRoots = [WebCheckoutAcceptance, MobileCheckoutAcceptance]

const createOrder = (step: Steps) => {
  const start = step.continue({ message: CheckoutAccepted, from: IntegrationEvents })
  const delivery = step.deliver({ value: start, to: OrderingCheckoutSub })
  const handled = step.consume({ value: delivery, by: OrderingCheckoutConsumer, operation: "consume checkout accepted and dispatch idempotent CreateOrderCommand", evidence: ev("evidence/UserCheckoutAcceptedIntegrationEventHandler.cs", "Request ID wraps CreateOrderCommand in IdentifiedCommand", "Handle") })
  const order = step.derive({ by: OrderingApi, value: handled, schema: OrderEvent, operation: "create order from checkout command" })
  const saved = step.write({ by: OrderingApi, value: order, to: OrderingSql, operation: "COMMIT new order and integration-event records", evidence: ev("evidence/CreateOrderCommandHandler.cs", "Order and OrderStarted event are saved in the unit of work", "Handle") })
  step.publish({ by: OrderingApi, value: saved, message: OrderStarted, to: IntegrationEvents, operation: "publish order started" })
  step.publish({ by: OrderingApi, value: saved, message: AwaitingValidation, to: IntegrationEvents, operation: "publish awaiting validation" })
  const basketDelivery = step.deliver({ value: saved, to: BasketOrderStartedSub })
  const basketHandled = step.consume({ value: basketDelivery, by: BasketOrderStartedConsumer, operation: "consume order started" })
  step.delete({ by: BasketOrderStartedConsumer, value: basketHandled, from: BasketRedis, operation: "DELETE checked-out basket" })
  const catalogDelivery = step.deliver({ value: saved, to: CatalogValidationSub })
  const catalogHandled = step.consume({ value: catalogDelivery, by: CatalogValidationConsumer, operation: "consume awaiting validation" })
  step.write({ by: CatalogValidationConsumer, value: catalogHandled, to: CatalogSql, operation: "validate and decrement catalog stock" })
  return catalogHandled
}

export const SuccessfulOrder = flow("asynchronous successful order", ({ step }) => {
  const catalogHandled = createOrder(step)
  const stock = step.derive({ by: CatalogValidationConsumer, value: catalogHandled, schema: StockEvent, operation: "create stock-confirmed result" })
  step.publish({ by: CatalogValidationConsumer, value: stock, message: StockConfirmed, to: IntegrationEvents, operation: "publish stock confirmed" })
  const orderDelivery = step.deliver({ value: stock, to: OrderingStockConfirmedSub }); const orderHandled = step.consume({ value: orderDelivery, by: OrderingStockConfirmedConsumer })
  step.write({ by: OrderingStockConfirmedConsumer, value: orderHandled, to: OrderingSql, operation: "UPDATE order to stock confirmed" })
  step.publish({ by: OrderingStockConfirmedConsumer, value: stock, message: StatusStockConfirmed, to: IntegrationEvents, operation: "publish stock-confirmed status" })
  const hubStock = step.deliver({ value: stock, to: HubStockConfirmedSub }); step.consume({ value: hubStock, by: HubStockConfirmedConsumer, operation: "notify clients of stock-confirmed status" })
  const paymentDelivery = step.deliver({ value: stock, to: PaymentStockConfirmedSub }); const payment = step.consume({ value: paymentDelivery, by: PaymentStockConfirmedConsumer, operation: "handle stock-confirmed payment" })
  const paid = step.derive({ by: PaymentStockConfirmedConsumer, value: payment, schema: PaymentEvent, operation: "create payment-succeeded result" })
  step.publish({ by: PaymentStockConfirmedConsumer, value: paid, message: PaymentSucceeded, to: IntegrationEvents, operation: "publish payment succeeded" })
  const paidDelivery = step.deliver({ value: paid, to: OrderingPaymentSucceededSub }); const paidHandled = step.consume({ value: paidDelivery, by: OrderingPaymentSucceededConsumer })
  step.write({ by: OrderingPaymentSucceededConsumer, value: paidHandled, to: OrderingSql, operation: "UPDATE order to paid" })
  const status = step.derive({ by: OrderingPaymentSucceededConsumer, value: paidHandled, schema: StatusEvent, operation: "create paid status" }); step.publish({ by: OrderingPaymentSucceededConsumer, value: status, message: PaidStatus, to: IntegrationEvents, operation: "publish paid status" })
  const hubPaid = step.deliver({ value: status, to: HubPaidSub }); step.consume({ value: hubPaid, by: HubPaidConsumer, operation: "notify clients of paid status" })
}, { continuesFrom: acceptedRoots })

export const StockRejectedOrder = flow("asynchronous stock rejection", ({ step }) => {
  const catalogHandled = createOrder(step)
  const stock = step.derive({ by: CatalogValidationConsumer, value: catalogHandled, schema: StockEvent, operation: "create stock-rejected result" }); step.publish({ by: CatalogValidationConsumer, value: stock, message: StockRejected, to: IntegrationEvents, operation: "publish stock rejected" })
  const delivery = step.deliver({ value: stock, to: OrderingStockRejectedSub }); const handled = step.consume({ value: delivery, by: OrderingStockRejectedConsumer })
  step.write({ by: OrderingStockRejectedConsumer, value: handled, to: OrderingSql, operation: "UPDATE order to cancelled (stock rejected)" })
  const status = step.derive({ by: OrderingStockRejectedConsumer, value: handled, schema: StatusEvent, operation: "create cancelled status" }); step.publish({ by: OrderingStockRejectedConsumer, value: status, message: CancelledStatus, to: IntegrationEvents, operation: "publish cancelled status" })
  const hub = step.deliver({ value: status, to: HubCancelledSub }); step.consume({ value: hub, by: HubCancelledConsumer, operation: "notify clients of cancelled status" })
}, { continuesFrom: acceptedRoots })

export const PaymentFailedOrder = flow("asynchronous payment failure", ({ step }) => {
  const start = step.continue({ message: StatusStockConfirmed, from: IntegrationEvents }); const paymentDelivery = step.deliver({ value: start, to: PaymentStockConfirmedSub }); const payment = step.consume({ value: paymentDelivery, by: PaymentStockConfirmedConsumer, operation: "handle stock-confirmed payment" })
  const failed = step.derive({ by: PaymentStockConfirmedConsumer, value: payment, schema: PaymentEvent, operation: "create payment-failed result" }); step.publish({ by: PaymentStockConfirmedConsumer, value: failed, message: PaymentFailed, to: IntegrationEvents, operation: "publish payment failed" })
  const delivery = step.deliver({ value: failed, to: OrderingPaymentFailedSub }); const handled = step.consume({ value: delivery, by: OrderingPaymentFailedConsumer })
  step.write({ by: OrderingPaymentFailedConsumer, value: handled, to: OrderingSql, operation: "UPDATE order to cancelled (payment failed)" })
  const status = step.derive({ by: OrderingPaymentFailedConsumer, value: handled, schema: StatusEvent, operation: "create cancelled status" }); step.publish({ by: OrderingPaymentFailedConsumer, value: status, message: CancelledStatus, to: IntegrationEvents, operation: "publish cancelled status" })
  const hub = step.deliver({ value: status, to: HubCancelledSub }); step.consume({ value: hub, by: HubCancelledConsumer, operation: "notify clients of cancelled status" })
}, { continuesFrom: [SuccessfulOrder] })

export default architecture({ BrowserCustomer, MobileCustomer, EShop, WebBff, MobileBff, BasketApi, OrderingApi, CatalogApi, PaymentApi, OrderingSignalRHub, BasketRedis, OrderingSql, CatalogSql, EventBus, WebCheckout, MobileCheckout, BasketCheckout, CheckoutAccepted, OrderStarted, AwaitingValidation, StockConfirmed, StockRejected, StatusStockConfirmed, PaymentSucceeded, PaymentFailed, PaidStatus, CancelledStatus, IntegrationEvents, OrderingCheckoutSub, BasketOrderStartedSub, CatalogValidationSub, OrderingStockConfirmedSub, OrderingStockRejectedSub, PaymentStockConfirmedSub, OrderingPaymentSucceededSub, OrderingPaymentFailedSub, HubStockConfirmedSub, HubPaidSub, HubCancelledSub, OrderingCheckoutConsumer, BasketOrderStartedConsumer, CatalogValidationConsumer, OrderingStockConfirmedConsumer, OrderingStockRejectedConsumer, PaymentStockConfirmedConsumer, OrderingPaymentSucceededConsumer, OrderingPaymentFailedConsumer, HubStockConfirmedConsumer, HubPaidConsumer, HubCancelledConsumer, WebCheckoutAcceptance, MobileCheckoutAcceptance, SuccessfulOrder, StockRejectedOrder, PaymentFailedOrder })
