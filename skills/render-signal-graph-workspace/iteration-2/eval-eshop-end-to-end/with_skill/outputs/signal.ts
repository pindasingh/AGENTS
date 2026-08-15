/** Dependency-free reference implementation of the Signal architecture DSL. */
export type Schema<A> = Readonly<{
  description: string
  shape: "primitive" | "literal" | "array" | "struct"
  value?: string | number | boolean
  item?: Schema<unknown>
  fields?: Readonly<Record<string, Schema<unknown>>>
  readonly __type?: A
}>
export type Infer<S> = S extends Schema<infer A> ? A : never

export const Schema = {
  String: Object.freeze({ description: "string", shape: "primitive" }) as Schema<string>,
  Number: Object.freeze({ description: "number", shape: "primitive" }) as Schema<number>,
  Boolean: Object.freeze({ description: "boolean", shape: "primitive" }) as Schema<boolean>,
  Literal: <const A extends string | number | boolean>(value: A): Schema<A> =>
    Object.freeze({ description: JSON.stringify(value), shape: "literal", value }),
  Array: <A>(item: Schema<A>): Schema<readonly A[]> =>
    Object.freeze({ description: `Array<${item.description}>`, shape: "array", item }),
  Struct: <const F extends Record<string, Schema<unknown>>>(fields: F): Schema<{ readonly [K in keyof F]: Infer<F[K]> }> =>
    Object.freeze({
      description: `{ ${Object.entries(fields).map(([key, value]) => `${key}: ${value.description}`).join(", ")} }`,
      shape: "struct",
      fields: Object.freeze({ ...fields }),
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
export type Topic = Base<"topic"> & Readonly<{ system: System; broker?: External; messages: readonly Message<unknown>[] }>
export type Subscription<A> = Base<"subscription"> & Readonly<{ topic: Topic; message: Message<A> }>
export type Consumer<A> = Base<"consumer"> & Readonly<{ service: Service; subscription: Subscription<A> }>
export type Declaration = Actor | System | Service | Store | External | Endpoint<unknown, unknown> | Message<unknown> | Topic | Subscription<unknown> | Consumer<unknown>

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

export type FlowStep = Readonly<{
  action: "request" | "respond" | "read" | "write" | "delete" | "derive" | "continue" | "publish" | "deliver" | "consume"
  from: Declaration | FlowStep
  to: Declaration | FlowStep
  contract?: Endpoint<unknown, unknown> | Message<unknown>
}>
type Value<A> = Readonly<{ source: FlowStep; request?: FlowStep; readonly value?: A }>
export type Flow = Readonly<{ kind: "flow"; name: string; description?: string; evidence?: readonly Evidence[]; continuesFrom?: readonly Flow[]; steps: readonly FlowStep[] }>

class Steps {
  readonly records: FlowStep[] = []
  private add<A>(action: FlowStep["action"], from: FlowStep["from"], to: FlowStep["to"], contract?: FlowStep["contract"], request?: FlowStep): Value<A> {
    const source: FlowStep = Object.freeze({ action, from, to, ...(contract ? { contract } : {}) })
    this.records.push(source)
    return Object.freeze({ source, ...(request ? { request } : {}) })
  }
  request<Req, Res>(from: Actor | Service | Consumer<unknown>, to: Endpoint<Req, Res>, _input?: Req): Value<Res> {
    const result = this.add<Res>("request", from, to, to)
    return Object.freeze({ source: result.source, request: result.source })
  }
  respond<Res>(value: Value<Res>, via: Endpoint<unknown, Res>): Value<Res> {
    if (!value.request) throw new Error(`Response via ${via.name} has no originating request`)
    return this.add("respond", via, value.request.from, via, value.request)
  }
  write<A>(value: Value<A>, to: Store): Value<A> { return this.add("write", value.source, to, undefined, value.request) }
  delete<A>(value: Value<A>, from: Store): Value<A> { return this.add("delete", value.source, from, undefined, value.request) }
  read<A>(from: Store, forStep: Value<unknown>): Value<A> { return this.add("read", from, forStep.source, undefined, forStep.request) }
  derive<A>(value: Value<unknown>, _schema: Schema<A>): Value<A> { return this.add("derive", value.source, value.source, undefined, value.request) }
  continue<A>(contract: Message<A>, from: Topic): Value<A> { return this.add("continue", from, contract, contract) }
  publish<A>(value: Value<A>, contract: Message<A>, to: Topic): Value<A> { return this.add("publish", value.source, to, contract, value.request) }
  deliver<A>(value: Value<A>, to: Subscription<A>): Value<A> { return this.add("deliver", value.source, to, to.message, value.request) }
  consume<A>(value: Value<A>, by: Consumer<A>): Value<A> { return this.add("consume", value.source, by, by.subscription.message, value.request) }
}

export const flow = (name: string, build: (context: { step: Steps }) => void, details: Omit<Flow, "kind" | "name" | "steps"> = {}): Flow => {
  const step = new Steps()
  build({ step })
  if (step.records.length === 0) throw new Error(`Flow ${name} must contain at least one step`)
  return Object.freeze({ kind: "flow", name, ...details, steps: Object.freeze([...step.records]) })
}

export const architecture = <const T extends Record<string, Declaration | Flow>>(declarations: T): Readonly<T> => Object.freeze(declarations)
