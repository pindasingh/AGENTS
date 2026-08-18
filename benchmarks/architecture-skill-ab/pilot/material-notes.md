# Pilot material notes

The historical pilot used `skills/build-signal-graph/evals/fixtures/eshop-checkout` because it was the only compact architecture evidence pack already present. Storing the fixture beside candidate A did not grant candidate A extra runtime access: both candidates received the same selected files. It does, however, make the fixture unsuitable as hidden confirmatory evidence because both candidate specifications include eShop expectations.

The fixture also asks for a payment-failure variant without supplying a payment-failure contract, consumer, state transition, terminal write, or notification. The correct evidence-backed treatment is an explicit unresolved branch; invented payment-failure details are forbidden. Some pilot assertions additionally overstate stock-rejection SignalR propagation and the final paid-status recipient. Reviewer disagreements about those claims are preserved rather than resolved after seeing outputs.

Future calibration may rebuild eShop evidence from the pinned public revision in `../materials.md`, but confirmatory cases must be unseen or deterministically renamed/structurally modified and adjudicated before generation.

Historical logs and browser records still contain the workspace's original path under `skills/architecture-diagram-pair-benchmark-workspace`. Those strings are retained as execution evidence; the files themselves were moved with `git mv` to the non-invokable benchmark location.
