# Validation commands and results

Run from the repository root with `OUT=skills/architecture-diagram-pair-benchmark-workspace/pilot/eshop-sequence/signal-render/outputs`.

```sh
tsc --strict --target ES2022 --module commonjs --outDir "$OUT/.architecture-build" "$OUT/architecture/signal.ts" "$OUT/architecture/architecture.ts"
```

Result: exit 0, no diagnostics (`typecheck.log` is empty).

```sh
node "$OUT/project-architecture.js" "$OUT/architecture/architecture.json"
```

Result: exit 0; data-only JSON projection written.

```sh
tsc --strict --target ES2022 --module commonjs --outDir "$OUT/.architecture-build/render" 'C:/Users/pinda/.pi/agent/skills/render-signal-graph/scripts/render.ts'
```

Result: exit 0, no diagnostics (`renderer-compile.log` is empty).

```sh
node "$OUT/.architecture-build/render/render.js" "$OUT/architecture/architecture.json" "$OUT/architecture/index.html"
```

Result: exit 0; self-contained HTML written (`render.log` is empty).

```sh
node 'C:/Users/pinda/.pi/agent/skills/render-signal-graph/tests/run-tests.js'
```

Result: exit 0 — `Signal DSL and interactive renderer tests passed`.

```sh
node -e "const fs=require('fs');const p=process.argv[1];const h=fs.readFileSync(p,'utf8');if(!h.includes('Content-Security-Policy')||!h.includes('HTTP 202 Accepted')||!h.includes('OrderPaymentSuccededIntegrationEvent'))process.exit(1); console.log('Offline HTML smoke checks passed:',h.length,'bytes')" "$OUT/architecture/index.html"
```

Result: exit 0 — `Offline HTML smoke checks passed: 36282 bytes`.
