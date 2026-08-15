declare const require: (id: string) => any
declare const process: { argv: string[]; cwd(): string; exitCode?: number }
const fs = require("fs") as { writeFileSync(path: string, data: string): void; mkdirSync(path: string, options: { recursive: boolean }): void }
const path = require("path") as { resolve(...parts: string[]): string; dirname(value: string): string }

type Evidence = { repository: string; revision: string; path: string; symbol?: string; observation: string; certainty: string }
type Decl = { kind: string; name: string; description?: string; evidence?: readonly Evidence[]; [key: string]: any }
type Step = { action: string; from: Decl | Step; to: Decl | Step; operation: string; contract?: Decl; evidence?: readonly Evidence[] }
type Flow = { kind: "flow"; name: string; description?: string; evidence?: readonly Evidence[]; continuesFrom?: readonly Flow[]; steps: readonly Step[] }
type Entry = { key: string; value: Decl | Flow }
type BoxEntry = { key: string; value: Decl }
type Interaction = { id: string; source: string; destination: string; action: string; contract?: string; flow: string; step: number; paths: string[]; evidence?: readonly Evidence[] }
type PathView = { id: string; name: string; flows: string[] }

const escapeHtml = (value: unknown): string => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!))
const safeJson = (value: unknown): string => JSON.stringify(value).replace(/[<>&\u2028\u2029]/g, c => ({ "<": "\\u003c", ">": "\\u003e", "&": "\\u0026", "\u2028": "\\u2028", "\u2029": "\\u2029" }[c] || c))
const short = (value: string, limit: number): string => value.length <= limit ? value : `${value.slice(0, limit - 1)}…`

export function renderArchitecture(model: Record<string, Decl | Flow>): string {
  if (!model || typeof model !== "object") throw new Error("Architecture module must export an object")
  const entries: Entry[] = Object.keys(model).sort().map(key => ({ key, value: model[key] }))
  if (!entries.length) throw new Error("Architecture is empty")
  const identities = new Map<object, Entry>()
  for (const entry of entries) {
    if (!entry.value || typeof entry.value !== "object") throw new Error(`Invalid declaration ${entry.key}`)
    if (identities.has(entry.value)) throw new Error(`Duplicate declaration object: ${entry.key}`)
    identities.set(entry.value, entry)
  }
  const declarations = entries.filter((entry): entry is BoxEntry => entry.value.kind !== "flow")
  const flows = entries.filter((entry): entry is { key: string; value: Flow } => entry.value.kind === "flow")
  const declarationIdentity = new Map<object, BoxEntry>()
  declarations.forEach(entry => declarationIdentity.set(entry.value, entry))

  const referencedBroker = new Set<object>()
  declarations.filter(x => x.value.kind === "topic" && x.value.broker).forEach(x => referencedBroker.add(x.value.broker))
  const boxKinds = new Set(["actor", "service", "store", "external"])
  const boxes = declarations.filter(entry => boxKinds.has(entry.value.kind) || (entry.value.kind === "topic" && !entry.value.broker))
  const boxByObject = new Map<object, BoxEntry>()
  boxes.forEach(entry => boxByObject.set(entry.value, entry))

  const flowEntry = new Map<object, { key: string; value: Flow }>()
  flows.forEach(entry => flowEntry.set(entry.value, entry))
  for (const entry of flows) for (const predecessor of entry.value.continuesFrom || []) {
    if (!flowEntry.has(predecessor)) throw new Error(`Flow ${entry.value.name} continues from a flow outside the root architecture`)
  }
  const successors = new Map<Flow, Flow[]>()
  flows.forEach(entry => successors.set(entry.value, []))
  flows.forEach(entry => (entry.value.continuesFrom || []).forEach(previous => successors.get(previous)!.push(entry.value)))
  const pathViews: PathView[] = []
  const walkBack = (flow: Flow, trail: Flow[] = []): Flow[][] => {
    if (trail.includes(flow)) throw new Error(`Flow continuation cycle at ${flow.name}`)
    const previous = flow.continuesFrom || []
    if (!previous.length) return [[flow]]
    return previous.flatMap(item => walkBack(item, [...trail, flow]).map(chain => [...chain, flow]))
  }
  const leaves = flows.filter(entry => !successors.get(entry.value)!.length)
  const chains = (leaves.length ? leaves : flows).flatMap(entry => walkBack(entry.value))
  chains.forEach((chain, index) => pathViews.push({ id: `path-${index + 1}`, name: chain.map(flow => flow.name).join(" → "), flows: chain.map(flow => flowEntry.get(flow)!.key) }))
  const pathsByFlow = new Map<string, string[]>()
  pathViews.forEach(item => item.flows.forEach(flow => pathsByFlow.set(flow, [...(pathsByFlow.get(flow) || []), item.id])))

  const normalizeBox = (reference: Decl): BoxEntry => {
    if (reference.kind === "endpoint") reference = reference.owner
    else if (reference.kind === "consumer") reference = reference.service
    else if (reference.kind === "subscription") reference = reference.topic.broker || reference.topic
    else if (reference.kind === "topic") reference = reference.broker || reference
    else if (reference.kind === "message") throw new Error(`Message ${reference.name} cannot be used as a component endpoint`)
    const box = boxByObject.get(reference)
    if (!box) throw new Error(`Relationship points outside the root architecture: ${reference.name}`)
    return box
  }
  const interactions: Interaction[] = []
  for (const flow of flows) flow.value.steps.forEach((step, index) => {
    let source: BoxEntry | undefined, destination: BoxEntry | undefined
    if (step.action === "request") { source = normalizeBox(step.from as Decl); destination = normalizeBox(step.to as Decl) }
    else if (step.action === "respond") { source = normalizeBox(step.from as Decl); destination = normalizeBox(step.to as Decl) }
    else if (["read", "write", "delete"].includes(step.action)) { source = normalizeBox(step.from as Decl); destination = normalizeBox(step.to as Decl) }
    else if (step.action === "publish") { source = normalizeBox(step.from as Decl); destination = normalizeBox(step.to as Decl) }
    else if (step.action === "consume") { source = normalizeBox(step.from as Decl); destination = normalizeBox(step.to as Decl) }
    else if (["derive", "continue", "deliver"].includes(step.action)) return
    else throw new Error(`Unsupported flow action: ${step.action}`)
    interactions.push({ id: `edge-${interactions.length + 1}`, source: source.key, destination: destination.key, action: step.operation, contract: step.contract?.name, flow: flow.key, step: index + 1, paths: pathsByFlow.get(flow.key) || [], evidence: step.evidence })
  })

  const byKey = new Map(boxes.map(box => [box.key, box]))
  const ranks = new Map<string, number>()
  boxes.filter(box => box.value.kind === "actor").forEach(box => ranks.set(box.key, 0))
  boxes.filter(box => box.value.kind === "service" && !interactions.some(edge => edge.destination === box.key)).forEach(box => ranks.set(box.key, 1))
  for (let pass = 0; pass < boxes.length; pass++) for (const edge of interactions) {
    const sourceRank = ranks.get(edge.source)
    if (sourceRank !== undefined && !ranks.has(edge.destination)) ranks.set(edge.destination, Math.min(6, sourceRank + 1))
  }
  boxes.forEach(box => {
    if (!ranks.has(box.key)) {
      if (box.value.kind === "actor") ranks.set(box.key, 0)
      else if (box.value.kind === "store") ranks.set(box.key, 5)
      else if (box.value.kind === "external" && referencedBroker.has(box.value)) ranks.set(box.key, 3)
      else ranks.set(box.key, 2)
    }
  })
  const columns = new Map<number, BoxEntry[]>()
  boxes.forEach(box => columns.set(ranks.get(box.key)!, [...(columns.get(ranks.get(box.key)!) || []), box]))
  columns.forEach(items => items.sort((a, b) => a.key.localeCompare(b.key)))
  const boxW = 210, boxH = 82, colGap = 190, rowGap = 100, margin = 70
  const positions = new Map<string, { x: number; y: number }>()
  columns.forEach((items, rank) => items.forEach((box, row) => positions.set(box.key, { x: margin + rank * (boxW + colGap), y: margin + row * (boxH + rowGap) })))
  const maxRank = Math.max(...[...columns.keys()], 0)
  const maxRows = Math.max(...[...columns.values()].map(items => items.length), 1)
  const canvasW = margin * 2 + (maxRank + 1) * boxW + maxRank * colGap
  const canvasH = margin * 2 + maxRows * boxH + (maxRows - 1) * rowGap

  const parallel = new Map<string, Interaction[]>()
  interactions.forEach(edge => { const key = `${edge.source}|${edge.destination}`; parallel.set(key, [...(parallel.get(key) || []), edge]) })
  const edgeSvg = interactions.map(edge => {
    const a = positions.get(edge.source)!, b = positions.get(edge.destination)!
    const siblings = parallel.get(`${edge.source}|${edge.destination}`)!
    const offset = (siblings.indexOf(edge) - (siblings.length - 1) / 2) * 13
    let x1: number, y1: number, x2: number, y2: number, d: string
    if (Math.abs(b.x - a.x) >= Math.abs(b.y - a.y)) {
      const forward = b.x >= a.x
      x1 = forward ? a.x + boxW : a.x; x2 = forward ? b.x : b.x + boxW
      y1 = a.y + boxH / 2 + offset; y2 = b.y + boxH / 2 + offset
      const bend = Math.max(65, Math.abs(x2 - x1) * .42)
      d = `M ${x1} ${y1} C ${x1 + (forward ? bend : -bend)} ${y1}, ${x2 - (forward ? bend : -bend)} ${y2}, ${x2} ${y2}`
    } else {
      const down = b.y >= a.y
      x1 = a.x + boxW / 2 + offset; x2 = b.x + boxW / 2 + offset
      y1 = down ? a.y + boxH : a.y; y2 = down ? b.y : b.y + boxH
      const bend = Math.max(65, Math.abs(y2 - y1) * .42)
      d = `M ${x1} ${y1} C ${x1} ${y1 + (down ? bend : -bend)}, ${x2} ${y2 - (down ? bend : -bend)}, ${x2} ${y2}`
    }
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2
    const label = short(edge.action, 42), labelW = Math.max(72, label.length * 7 + 18)
    return `<g class="interaction" tabindex="0" role="button" aria-label="${escapeHtml(edge.action)} from ${escapeHtml(byKey.get(edge.source)!.value.name)} to ${escapeHtml(byKey.get(edge.destination)!.value.name)}" data-edge="${edge.id}" data-source="${escapeHtml(edge.source)}" data-destination="${escapeHtml(edge.destination)}" data-paths="${escapeHtml(edge.paths.join(" "))}"><path d="${d}"/><rect class="edge-label-bg" x="${mx - labelW / 2}" y="${my - 13}" width="${labelW}" height="23" rx="6"/><text class="edge-label" x="${mx}" y="${my + 3}">${escapeHtml(label)}</text><title>${escapeHtml(`${edge.action} · ${edge.flow} step ${edge.step}`)}</title></g>`
  }).join("")
  const nodeSvg = boxes.map(box => {
    const p = positions.get(box.key)!
    const detail = box.value.kind === "store" ? box.value.engine : box.value.kind === "service" ? (box.value.technology || []).join(", ") : box.value.kind
    return `<g class="component" tabindex="0" role="button" data-node="${escapeHtml(box.key)}" aria-label="${escapeHtml(box.value.name)} ${escapeHtml(box.value.kind)}"><rect x="${p.x}" y="${p.y}" width="${boxW}" height="${boxH}" rx="12"/><text class="node-name" x="${p.x + 15}" y="${p.y + 34}">${escapeHtml(short(box.value.name, 27))}</text><text class="node-kind" x="${p.x + 15}" y="${p.y + 58}">${escapeHtml(short(detail || box.value.kind, 30))}</text><title>${escapeHtml(box.value.name)}</title></g>`
  }).join("")
  const data = safeJson({ paths: pathViews, interactions, nodes: boxes.map(box => ({ key: box.key, name: box.value.name, kind: box.value.kind, description: box.value.description || "", evidence: box.value.evidence || [] })) })
  const counts = `<b>${boxes.length}</b> components · <b>${interactions.length}</b> interactions · <b>${pathViews.length}</b> end-to-end paths`

  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-signal-graph'; base-uri 'none'; form-action 'none'"><title>Signal architecture paths</title><style>
:root{color-scheme:dark;--bg:#07111f;--panel:#0d1b2d;--box:#132743;--line:#6f8daf;--text:#eef6ff;--muted:#9aabc1;--active:#54ead2;--dim:.12}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px system-ui,sans-serif}header{padding:18px 24px;border-bottom:1px solid #203653;display:flex;align-items:center;gap:18px;flex-wrap:wrap}h1{font-size:1.35rem;margin:0}header p{margin:0;color:var(--muted)}button{background:#122640;color:var(--text);border:1px solid #385679;border-radius:7px;padding:8px 11px;cursor:pointer}button:hover,button.active{border-color:var(--active);color:var(--active)}.workspace{display:grid;grid-template-columns:minmax(0,1fr) 340px;height:calc(100vh - 69px)}.canvas{overflow:auto;padding:18px}.canvas svg{min-width:100%;height:auto;background:var(--panel);border:1px solid #203653;border-radius:12px}.component rect{fill:var(--box);stroke:#6d91b9;stroke-width:2}.component,.interaction{cursor:pointer;transition:opacity .18s}.node-name{fill:var(--text);font-weight:700;font-size:15px}.node-kind{fill:var(--muted);font-size:12px}.interaction path{fill:none;stroke:var(--line);stroke-width:2;marker-end:url(#arrow)}.edge-label-bg{fill:#0a1728;stroke:#35516f}.edge-label{fill:#c7d7e9;font-size:11px;text-anchor:middle}.dim{opacity:var(--dim)}.interaction.selected{opacity:1}.interaction.selected path{stroke:var(--active);stroke-width:5;marker-end:url(#active-arrow)}.interaction.selected .edge-label-bg{stroke:var(--active);fill:#102f36}.interaction.selected .edge-label{fill:#bafff4;font-weight:700}.component.selected{opacity:1}.component.selected rect{stroke:var(--active);stroke-width:4;filter:drop-shadow(0 0 7px #33bda8)}aside{border-left:1px solid #203653;background:#0a1627;padding:18px;overflow:auto}aside h2{margin-top:0}.hint{color:var(--muted);line-height:1.5}.path-list{display:grid;gap:8px}.path-list button{text-align:left;line-height:1.35}.details{margin-top:18px;border-top:1px solid #203653;padding-top:15px}.details code{color:#8fe8d8;overflow-wrap:anywhere}.legend{display:flex;gap:12px;margin-top:10px;color:var(--muted);font-size:12px}.swatch{display:inline-block;width:20px;border-top:3px solid var(--line);vertical-align:middle}.swatch.active{border-color:var(--active);border-width:5px}@media(max-width:850px){.workspace{grid-template-columns:1fr;height:auto}.canvas{height:72vh}aside{border-left:0;border-top:1px solid #203653;min-height:28vh}}@media print{aside,header button{display:none}.workspace{display:block}.canvas{overflow:visible}.canvas svg{width:100%}}
</style></head><body><header><h1>Architecture interaction map</h1><p>${counts}</p><button id="reset">Show all</button><div class="legend"><span><i class="swatch active"></i> selected path</span><span><i class="swatch"></i> other architecture</span></div></header><div class="workspace"><main class="canvas"><svg viewBox="0 0 ${canvasW} ${canvasH}" role="group" aria-label="Interactive architecture component and interaction graph"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="#6f8daf"/></marker><marker id="active-arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="#54ead2"/></marker></defs>${edgeSvg}${nodeSvg}</svg></main><aside><h2 id="selection-title">Explore paths</h2><p id="hint" class="hint">Select any HTTP, persistence, transport, or downstream interaction. If it belongs to several end-to-end paths, choose the path to highlight. Select a component to see every path that touches it.</p><div id="paths" class="path-list"></div><div id="details" class="details"></div></aside></div><script id="architecture-data" type="application/json">${data}</script><script nonce="signal-graph">(()=>{const data=JSON.parse(document.querySelector('#architecture-data').textContent),edges=[...document.querySelectorAll('.interaction')],nodes=[...document.querySelectorAll('.component')],paths=document.querySelector('#paths'),title=document.querySelector('#selection-title'),details=document.querySelector('#details');const byPath=new Map(data.paths.map(p=>[p.id,p]));function clear(){edges.forEach(e=>e.classList.remove('dim','selected'));nodes.forEach(n=>n.classList.remove('dim','selected'));paths.replaceChildren();details.textContent='';title.textContent='Explore paths'}function selectPath(id){const path=byPath.get(id),activeNodes=new Set();edges.forEach(e=>{const on=e.dataset.paths.split(' ').includes(id);e.classList.toggle('selected',on);e.classList.toggle('dim',!on);if(on){activeNodes.add(e.dataset.source);activeNodes.add(e.dataset.destination)}});nodes.forEach(n=>{const on=activeNodes.has(n.dataset.node);n.classList.toggle('selected',on);n.classList.toggle('dim',!on)});[...paths.children].forEach(b=>b.classList.toggle('active',b.dataset.path===id));title.textContent='Highlighted end-to-end path';details.replaceChildren();const heading=document.createElement('b'),explanation=document.createElement('p');heading.textContent=path.name;explanation.className='hint';explanation.textContent='Every bright arrow is an interaction touched by this operation path. All other architecture remains visible.';details.append(heading,explanation)}function offer(ids,label){const unique=[...new Set(ids)].filter(Boolean);title.textContent=label;paths.replaceChildren();if(!unique.length){const empty=document.createElement('p');empty.className='hint';empty.textContent='No end-to-end path uses this item.';details.replaceChildren(empty);return}unique.forEach(id=>{const b=document.createElement('button');b.dataset.path=id;b.textContent=byPath.get(id).name;b.addEventListener('click',()=>selectPath(id));paths.append(b)});if(unique.length===1)selectPath(unique[0])}edges.forEach(e=>{const act=()=>{const item=data.interactions.find(x=>x.id===e.dataset.edge);offer(item.paths,'Interaction: '+item.action);const paragraph=document.createElement('p'),code=document.createElement('code');code.textContent=item.source+' → '+item.destination;paragraph.append(code);details.append(paragraph)};e.addEventListener('click',act);e.addEventListener('keydown',x=>{if(x.key==='Enter'||x.key===' '){x.preventDefault();act()}})});nodes.forEach(n=>{const act=()=>{const ids=data.interactions.filter(e=>e.source===n.dataset.node||e.destination===n.dataset.node).flatMap(e=>e.paths),node=data.nodes.find(x=>x.key===n.dataset.node);offer(ids,'Component: '+node.name);const description=document.createElement('p');description.className='hint';description.textContent=node.kind+(node.description?' · '+node.description:'');details.append(description)};n.addEventListener('click',act);n.addEventListener('keydown',x=>{if(x.key==='Enter'||x.key===' '){x.preventDefault();act()}})});document.querySelector('#reset').addEventListener('click',clear)})()</script></body></html>`
}

export function run(argv: string[]): void {
  if (argv.length !== 2) throw new Error("Usage: node render.js <compiled-architecture.js> <architecture/index.html>")
  const input = path.resolve(process.cwd(), argv[0]), output = path.resolve(process.cwd(), argv[1])
  const loaded = require(input), model = loaded.default || loaded.architecture || loaded
  const html = renderArchitecture(model)
  fs.mkdirSync(path.dirname(output), { recursive: true })
  fs.writeFileSync(output, html)
}
if (process.argv[1] && /render(?:\.js)?$/.test(process.argv[1])) { try { run(process.argv.slice(2)) } catch (error) { console.error(error instanceof Error ? error.message : String(error)); process.exitCode = 1 } }
