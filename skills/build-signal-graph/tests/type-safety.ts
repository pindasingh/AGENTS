import {
  Schema, actor, consumer, endpoint, external, flow, message,
  service, subscription, system, topic,
} from "../assets/signal.js"

const User = actor({ name: "User" })
const App = system({ name: "App" })
const Api = service({ system: App, name: "API" })
const Worker = service({ system: App, name: "Worker" })
const Vendor = external({ name: "Vendor" })
const Create = endpoint({
  owner: Api, name: "Create", method: "POST", path: "/items",
  request: Schema.Struct({ quantity: Schema.Number }),
  response: Schema.Struct({ id: Schema.String }),
})
const Notify = endpoint({
  owner: Vendor, name: "Notify", method: "POST", path: "/notify",
  request: Schema.Struct({ id: Schema.String }),
  response: Schema.Struct({ accepted: Schema.Boolean }),
})
const Created = message({ name: "item.created", schema: Schema.Struct({ id: Schema.String }) })
const Events = topic({ system: App, name: "events", messages: [Created] })
const CreatedSubscription = subscription({ name: "created", topic: Events, message: Created })
const CreatedConsumer = consumer({ name: "created", service: Worker, subscription: CreatedSubscription })

flow("valid", ({ step }) => {
  const response = step.request(User, Create, { quantity: 1 })
  const published = step.publish(response, Created, Events)
  const delivered = step.deliver(published, CreatedSubscription)
  const consumed = step.consume(delivered, CreatedConsumer)
  step.request(CreatedConsumer, Notify, consumed.value)
})

flow("invalid request", ({ step }) => {
  // @ts-expect-error quantity must be a number
  step.request(User, Create, { quantity: "one" })
})

const WrongMessage = message({ name: "wrong", schema: Schema.Struct({ quantity: Schema.Number }) })
flow("invalid publication", ({ step }) => {
  const response = step.request(User, Create, { quantity: 1 })
  // @ts-expect-error response has {id}, but WrongMessage requires {quantity}
  step.publish(response, WrongMessage, Events)
})
