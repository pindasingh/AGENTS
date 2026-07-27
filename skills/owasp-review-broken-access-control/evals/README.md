# Evaluation suite

This directory is development support, not runtime assessment output.

- Skill version: `0.9.1`
- Assessment contract: `1.4`
- Eval suite: `2.0.0`
- Cases: 22 behavioral evaluations
- Canonical cases: file-backed vulnerable and secure twins for all three OWASP A01:2025 attack scenarios
- Scope-efficiency controls: excluded static public site, supporting-only client MFE, and selective review of a mixed repository portfolio
- Mode controls: triage stops early, focused is the default, and comprehensive coverage/artifacts require an explicit request
- Progressive-loading controls: focused runs load only evidence-supported concern references
- Format control: one canonical JSON assessment for every mode; presentation conversion is downstream
- Portability control: direct harness-native JSON output in an enterprise environment that prohibits scripts and subprocesses
- Extended cases: false-positive, parser/method, business-flow, CORS/CSRF, mixed Node, secure ASP.NET, layered APIM/BFF, material evidence checkpoint, and architecture-neutral event delegation
- Evaluation-corpus control: explicitly supplied synthetic authorization corpora remain eligible without implying production exposure, and blind protocols preserve answer isolation
- File-backed cases: `fixtures/official-a01/`, `fixtures/api-business/`, `fixtures/evaluation-corpus/`, `fixtures/ambiguous-admin/`, `fixtures/static-public-site/`, `fixtures/client-only-orders-mfe/`, `fixtures/scope-portfolio/`, `fixtures/mixed-node-app/`, `fixtures/secure-dotnet-app/`, and `fixtures/layered-enterprise/`

## OWASP source coverage

| Source pattern | Internal controls |
|---|---|
| A01:2025 scenario 1 — account IDOR | neutral vulnerable and owner-scoped secure twins |
| A01:2025 scenario 2 — force browsing | neutral vulnerable and fallback/Admin-policy secure twins |
| A01:2025 scenario 3 — client-side control | neutral vulnerable and trusted-server-policy secure twins |
| API1:2023 — object authorization | account and multi-tenant invoice cases |
| API3/API5/API6:2023 | vulnerable and secure refund property/function/workflow twins |
| WSTG v4.2 | method/parser, business-flow, CORS/CSRF, gateway, and evidence-checkpoint cases |

This directory contains only data and fixtures. It intentionally provides no runner, helper script, executable validator, or renderer. The outer evaluation harness is responsible for loading `evals.json`, staging fixture files, capturing outputs/timing and file-access events, and grading assertions.

Apply these suite-wide assertions to every completed run in addition to each case's assertions:

1. exactly one output artifact contains one parseable JSON document and no Markdown, HTML, SARIF, or second presentation;
2. `schemaVersion` is `1.4`, `assessment.mode` is valid, and all seven required top-level fields exist;
3. triage leaves authorization model, coverage, findings, and gaps empty; focused mode includes only selected/applicable coverage; comprehensive mode contains each of the 19 branches exactly once;
4. IDs are unique, references resolve in both directions, statuses are valid, and security outcome/trace completeness agree with findings, paths, coverage, and gaps;
5. transcript evidence supports scope-efficiency and reference-loading assertions; final-output prose alone cannot prove which files were opened;
6. an oracle-isolation assertion passes only when file-access events prove the answer key was not opened before the result was frozen.

Behavioral runs belong in a sibling workspace outside the distributable skill, for example:

```text
owasp-review-broken-access-control-eval-workspace/
  iteration-1/
    <eval-id>/
      with_skill/
        subject/
        outputs/
        response.txt
        timing.json
      without_skill/
        subject/
        outputs/
        response.txt
        timing.json
```

Do not write generated assessments, model transcripts, timing, grading, benchmark, or reviewer artifacts into the runtime skill directory. `evals.json` and fixtures are versioned inputs; run artifacts are disposable external evidence.

Production-quality claims require outer-harness model runs, baseline comparison, assertion grading, completion/timing review, and representative application repositories. Review transcripts and token counts as well as final answers: passing behavior must avoid recursive exploration of excluded repositories, unrelated concern-reference loads, silent focused-to-comprehensive upgrades, presentation-format output, and answer-oracle access before a benchmark result is frozen. For the portability case, any attempt to execute or create a script is a failure even if the final assessment looks correct.
