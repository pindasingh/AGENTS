import { Schema, actor, endpoint, flow, service, store, system } from "../assets/signal.js"
const assert = (condition: unknown, message: string): void => { if (!condition) throw new Error(message) }
const User = actor({ name: "User" })
const App = system({ name: "App" })
const Api = service({ name: "API", system: App })
const Data = store({ name: "Data", system: App, engine: "memory" })
const Create = endpoint({ owner: Api, name: "Create", method: "POST", path: "/", request: Schema.String, response: Schema.String })
const scenario = flow("identity", ({ step }) => {
  const requested = step.request({ from: User, to: Create, input: "input" })
  const written = step.write({ by: Api, value: requested, to: Data, operation: "INSERT item" })
  step.delete({ by: Api, value: written, from: Data, operation: "DELETE item" })
  step.respond({ value: requested, via: Create })
})
assert(scenario.steps[0].from === User && scenario.steps[0].to === Create, "request retains caller and endpoint")
assert(scenario.steps[1].from === Api && scenario.steps[1].to === Data, "write retains executor and store")
assert(scenario.steps[1].operation === "INSERT item", "write retains operation")
assert(scenario.steps[2].action === "delete" && scenario.steps[2].to === Data, "delete retains store")
assert(scenario.steps[3].to === User && scenario.steps[3].contract === Create, "response resolves caller")
