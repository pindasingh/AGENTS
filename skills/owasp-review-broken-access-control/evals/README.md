# Evaluation suite

This directory is development support, not runtime assessment output.

- Skill version: `0.7.0`
- Assessment contract: `1.3`
- Eval suite: `1.7.0`
- Canonical cases: all three OWASP A01:2025 attack scenarios
- Scope-efficiency controls: excluded static public site, supporting-only client MFE, and selective review of a mixed repository portfolio
- Portability control: direct harness-native assessment/report output in an enterprise environment that prohibits scripts and subprocesses
- Extended cases: false-positive, parser/method, business-flow, CORS/CSRF, mixed Node, secure ASP.NET, layered APIM/BFF, material evidence checkpoint, and architecture-neutral event delegation
- File-backed cases: `fixtures/static-public-site/`, `fixtures/client-only-orders-mfe/`, `fixtures/scope-portfolio/`, `fixtures/mixed-node-app/`, `fixtures/secure-dotnet-app/`, and `fixtures/layered-enterprise/`

This directory contains only data and fixtures. It intentionally provides no runner, helper script, executable validator, or renderer. The outer evaluation harness is responsible for loading `evals.json`, staging fixture files, capturing outputs/timing, and grading assertions.

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

Do not write generated reports, model transcripts, timing, grading, benchmark, or reviewer artifacts into the runtime skill directory. `evals.json` and fixtures are versioned inputs; run artifacts are disposable external evidence.

Production-quality claims require outer-harness model runs, baseline comparison, assertion grading, completion/timing review, and representative application repositories. For scope-efficiency cases, review transcripts and token counts as well as final answers: passing behavior must avoid recursive exploration of excluded repositories, not merely omit them from the final report. For the portability case, any attempt to execute or create a script is a failure even if the final report looks correct.
