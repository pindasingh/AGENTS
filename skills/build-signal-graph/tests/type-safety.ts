import { Schema, actor, consumer, endpoint, external, flow, message, service, subscription, system, topic } from "../assets/signal.js"

const User = actor({ name: "User" })
const App = system({ name: "App" })
const Api = service({ system: App, name: "API" })
const Worker = service({ system: App, name: "Worker" })
const Broker = external({ name: "Broker" })
const Vendor = external({ name: "Vendor" })
const Create = endpoint({ owner: Api, name: "Create", method: "POST", path: "/items", request: Schema.Struct({ quantity: Schema.Number }), response: Schema.Struct({ id: Schema.String }) })
const Notify = endpoint({ owner: Vendor, name: "Notify", method: "POST", path: "/notify", request: Schema.Struct({ id: Schema.String }), response: Schema.Struct({ accepted: Schema.Boolean }) })
const Created = message({ name: "item.created", schema: Schema.Struct({ id: Schema.String }) })
const Events = topic({ system: App, broker: Broker, name: "events", messages: [Created] })
const CreatedSubscription = subscription({ name: "created", topic: Events, message: Created })
const CreatedConsumer = consumer({ name: "created", service: Worker, subscription: CreatedSubscription })

flow("valid", ({ step }) => {
  const response = step.request({ from: User, to: Create, input: { quantity: 1 } })
  const published = step.publish({ by: Api, value: response, message: Created, to: Events })
  const delivered = step.deliver({ value: published, to: CreatedSubscription })
  const consumed = step.consume({ value: delivered, by: CreatedConsumer })
  step.request({ from: CreatedConsumer, to: Notify, input: consumed.value })
})

flow("invalid request", ({ step }) => {
  // @ts-expect-error quantity must be a number
  step.request({ from: User, to: Create, input: { quantity: "one" } })
})

const WrongMessage = message({ name: "wrong", schema: Schema.Struct({ quantity: Schema.Number }) })
flow("invalid publication", ({ step }) => {
  const response = step.request({ from: User, to: Create, input: { quantity: 1 } })
  // @ts-expect-error response has {id}, but WrongMessage requires {quantity}
  step.publish({ by: Api, value: response, message: WrongMessage, to: Events })
})
