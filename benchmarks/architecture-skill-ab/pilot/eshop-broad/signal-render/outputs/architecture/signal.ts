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
  Literal: <const A extends string | number | boolean>(value: A): Schema<A> => Object.freeze({ description: JSON.stringify(value), shape: "literal", value }),
  Array: <A>(item: Schema<A>): Schema<readonly A[]> => Object.freeze({ description: `Array<${item.description}>`, shape: "array", item }),
  Struct: <const F extends Record<string, Schema<unknown>>>(fields: F): Schema<{ readonly [K in keyof F]: Infer<F[K]> }> => Object.freeze({
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
export type Endpoint<Req, Res> = Base<"endpoint"> & Readonly<{ owner: Service | External; method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "OPTIONS" | "HEAD"; path: string; request: Schema<Req>; response: Schema<Res> }>
export type Message<A> = Base<"message"> & Readonly<{ schema: Schema<A> }>
export type Topic = Base<"topic"> & Readonly<{ system: System; broker?: External; messages: readonly Message<unknown>[] }>
export type Subscription<A> = Base<"subscription"> & Readonly<{ topic: Topic; message: Message<A> }>
export type Consumer<A> = Base<"consumer"> & Readonly<{ service: Service; subscription: Subscription<A> }>
export type Declaration = Actor | System | Service | Store | External | Endpoint<unknown, unknown> | Message<unknown> | Topic | Subscription<unknown> | Consumer<unknown>
export type Executor = Actor | Service | Consumer<unknown>

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

export type FlowAction = "request" | "respond" | "read" | "write" | "delete" | "derive" | "continue" | "publish" | "deliver" | "consume"
export type FlowStep = Readonly<{
  action: FlowAction
  from: Declaration | FlowStep
  to: Declaration | FlowStep
  operation: string
  contract?: Endpoint<unknown, unknown> | Message<unknown>
  evidence?: readonly Evidence[]
}>
type Value<A> = Readonly<{ source: FlowStep; request?: FlowStep; readonly value?: A }>
export type Flow = Readonly<{ kind: "flow"; name: string; description?: string; evidence?: readonly Evidence[]; continuesFrom?: readonly Flow[]; steps: readonly FlowStep[] }>

type StepEvidence = { operation: string; evidence?: readonly Evidence[] }
export class Steps {
  readonly records: FlowStep[] = []
  private add<A>(action: FlowAction, from: FlowStep["from"], to: FlowStep["to"], operation: string, contract?: FlowStep["contract"], evidence?: readonly Evidence[], request?: FlowStep): Value<A> {
    const source: FlowStep = Object.freeze({ action, from, to, operation, ...(contract ? { contract } : {}), ...(evidence ? { evidence } : {}) })
    this.records.push(source)
    return Object.freeze({ source, ...(request ? { request } : {}) })
  }
  request<Req, Res>(input: { from: Executor; to: Endpoint<Req, Res>; input?: Req; evidence?: readonly Evidence[] }): Value<Res> {
    const result = this.add<Res>("request", input.from, input.to, `${input.to.method} ${input.to.path}`, input.to, input.evidence)
    return Object.freeze({ source: result.source, request: result.source })
  }
  respond<Res>(input: { value: Value<Res>; via: Endpoint<unknown, Res>; operation?: string; evidence?: readonly Evidence[] }): Value<Res> {
    if (!input.value.request) throw new Error(`Response via ${input.via.name} has no originating request`)
    return this.add("respond", input.via, input.value.request.from, input.operation || `${input.via.response.description} response`, input.via, input.evidence, input.value.request)
  }
  read<A>(input: { by: Service | Consumer<unknown>; from: Store; forStep: Value<unknown>; schema: Schema<A> } & StepEvidence): Value<A> {
    return this.add("read", input.by, input.from, input.operation, undefined, input.evidence, input.forStep.request)
  }
  write<A>(input: { by: Service | Consumer<unknown>; value: Value<A>; to: Store } & StepEvidence): Value<A> {
    return this.add("write", input.by, input.to, input.operation, undefined, input.evidence, input.value.request)
  }
  delete<A>(input: { by: Service | Consumer<unknown>; value: Value<A>; from: Store } & StepEvidence): Value<A> {
    return this.add("delete", input.by, input.from, input.operation, undefined, input.evidence, input.value.request)
  }
  derive<A>(input: { by: Service | Consumer<unknown>; value: Value<unknown>; schema: Schema<A> } & StepEvidence): Value<A> {
    return this.add("derive", input.by, input.by, input.operation, undefined, input.evidence, input.value.request)
  }
  continue<A>(input: { message: Message<A>; from: Topic; operation?: string; evidence?: readonly Evidence[] }): Value<A> {
    return this.add("continue", input.from, input.message, input.operation || `continue ${input.message.name}`, input.message, input.evidence)
  }
  publish<A>(input: { by: Service | Consumer<unknown>; value: Value<A>; message: Message<A>; to: Topic } & Omit<StepEvidence, "operation"> & { operation?: string }): Value<A> {
    return this.add("publish", input.by, input.to, input.operation || `publish ${input.message.name}`, input.message, input.evidence, input.value.request)
  }
  deliver<A>(input: { value: Value<A>; to: Subscription<A>; operation?: string; evidence?: readonly Evidence[] }): Value<A> {
    return this.add("deliver", input.to.topic, input.to, input.operation || `deliver ${input.to.message.name}`, input.to.message, input.evidence, input.value.request)
  }
  consume<A>(input: { value: Value<A>; by: Consumer<A>; operation?: string; evidence?: readonly Evidence[] }): Value<A> {
    return this.add("consume", input.by.subscription.topic, input.by, input.operation || `consume ${input.by.subscription.message.name}`, input.by.subscription.message, input.evidence, input.value.request)
  }
}

export const flow = (name: string, build: (context: { step: Steps }) => void, details: Omit<Flow, "kind" | "name" | "steps"> = {}): Flow => {
  const step = new Steps()
  build({ step })
  if (step.records.length === 0) throw new Error(`Flow ${name} must contain at least one step`)
  return Object.freeze({ kind: "flow", name, ...details, steps: Object.freeze([...step.records]) })
}

export const architecture = <const T extends Record<string, Declaration | Flow>>(declarations: T): Readonly<T> => Object.freeze(declarations)
