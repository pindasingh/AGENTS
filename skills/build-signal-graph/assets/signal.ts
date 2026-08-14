/** A dependency-free reference implementation of the Signal architecture DSL. */
export type Schema<A> = { readonly description: string; readonly __type?: A }
export type Infer<S> = S extends Schema<infer A> ? A : never

export const Schema = {
  String: { description: "string" } as Schema<string>,
  Number: { description: "number" } as Schema<number>,
  Boolean: { description: "boolean" } as Schema<boolean>,
  Literal: <const A extends string | number | boolean>(value: A): Schema<A> => ({ description: JSON.stringify(value) }),
  Array: <A>(item: Schema<A>): Schema<readonly A[]> => ({ description: `Array<${item.description}>` }),
  Struct: <const F extends Record<string, Schema<unknown>>>(fields: F): Schema<{ readonly [K in keyof F]: Infer<F[K]> }> => ({
    description: `{ ${Object.entries(fields).map(([key, value]) => `${key}: ${value.description}`).join(", ")} }`,
  }),
}

type Certainty = "observed" | "inferred" | "unknown"
export type Evidence = Readonly<{ repository: string; revision: string; path: string; symbol?: string; observation: string; certainty: Certainty }>
export const evidence = (value: Evidence): Evidence => Object.freeze(value)

type Base<K extends string> = Readonly<{ kind: K; name: string; description?: string; evidence?: readonly Evidence[] }>
export type Actor = Base<"actor">
export type System = Base<"system">
export type Service = Base<"service"> & Readonly<{ system: System; technology?: readonly string[] }>
export type Store = Base<"store"> & Readonly<{ system: System; engine: string }>
export type External = Base<"external">
export type Endpoint<Req, Res> = Base<"endpoint"> & Readonly<{
  owner: Service | External
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "OPTIONS" | "HEAD"
  path: string
  request: Schema<Req>
  response: Schema<Res>
}>
export type Message<A> = Base<"message"> & Readonly<{ schema: Schema<A> }>
export type Topic = Base<"topic"> & Readonly<{ system: System; messages: readonly Message<unknown>[] }>
export type Subscription<A> = Base<"subscription"> & Readonly<{ topic: Topic; message: Message<A> }>
export type Consumer<A> = Base<"consumer"> & Readonly<{ service: Service; subscription: Subscription<A> }>

const declared = <T>(kind: string, value: object): T => Object.freeze({ kind, ...value }) as T
export const actor = (value: Omit<Actor, "kind">): Actor => declared("actor", value)
export const system = (value: Omit<System, "kind">): System => declared("system", value)
export const service = (value: Omit<Service, "kind">): Service => declared("service", value)
export const store = (value: Omit<Store, "kind">): Store => declared("store", value)
export const external = (value: Omit<External, "kind">): External => declared("external", value)
export const endpoint = <Req, Res>(value: Omit<Endpoint<Req, Res>, "kind">): Endpoint<Req, Res> => declared("endpoint", value)
export const message = <A>(value: Omit<Message<A>, "kind">): Message<A> => declared("message", value)
export const topic = (value: Omit<Topic, "kind">): Topic => declared("topic", value)
export const subscription = <A>(value: Omit<Subscription<A>, "kind">): Subscription<A> => declared("subscription", value)
export const consumer = <A>(value: Omit<Consumer<A>, "kind">): Consumer<A> => declared("consumer", value)

type Value<A> = Readonly<{ step: number; value?: A }>
type FlowStep = Readonly<{ action: string; from: string; to: string; contract?: string }>
export type Flow = Readonly<{ kind: "flow"; name: string; steps: readonly FlowStep[] }>

class Steps {
  readonly records: FlowStep[] = []
  private add<A>(action: string, from: { name: string }, to: { name: string }, contract?: string): Value<A> {
    this.records.push(Object.freeze({ action, from: from.name, to: to.name, ...(contract ? { contract } : {}) }))
    return Object.freeze({ step: this.records.length })
  }
  request<Req, Res>(from: Actor | Service | Consumer<unknown>, to: Endpoint<Req, Res>, _input?: Req): Value<Res> {
    return this.add("request", from, to, `${to.method} ${to.path}`)
  }
  respond<Res>(value: Value<unknown>, via: Endpoint<unknown, Res>): Value<Res> {
    return this.add("respond", via, { name: `caller of ${via.name}` }, `response ${via.method} ${via.path}`)
  }
  write<A>(value: Value<A>, to: Store): Value<A> { return this.add("write", { name: `step ${value.step}` }, to) }
  read<A>(from: Store, forStep: Value<unknown>): Value<A> { return this.add("read", from, { name: `step ${forStep.step}` }) }
  publish<A>(value: Value<A>, contract: Message<A>, to: Topic): Value<A> { return this.add("publish", { name: `step ${value.step}` }, to, contract.name) }
  deliver<A>(value: Value<A>, to: Subscription<A>): Value<A> { return this.add("deliver", { name: `step ${value.step}` }, to, to.message.name) }
  consume<A>(value: Value<A>, by: Consumer<A>): Value<A> { return this.add("consume", { name: `step ${value.step}` }, by, by.subscription.message.name) }
}

export const flow = (name: string, build: (context: { step: Steps }) => void): Flow => {
  const step = new Steps()
  build({ step })
  if (step.records.length === 0) throw new Error(`Flow ${name} must contain at least one step`)
  return Object.freeze({ kind: "flow", name, steps: Object.freeze([...step.records]) })
}

export const architecture = <const T extends Record<string, Actor | System | Service | Store | External | Endpoint<unknown, unknown> | Message<unknown> | Topic | Subscription<unknown> | Consumer<unknown> | Flow>>(declarations: T): Readonly<T> => Object.freeze(declarations)
