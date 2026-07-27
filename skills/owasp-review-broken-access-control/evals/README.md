# Evaluation suite

This directory is development support, not runtime assessment output.

- Skill version: `0.6.0`
- Assessment contract: `1.3`
- Eval suite: `1.6.0`
- Canonical cases: all three OWASP A01:2025 attack scenarios
- Scope-efficiency controls: excluded static public site, supporting-only client MFE, and selective review of a mixed repository portfolio
- Extended cases: false-positive, parser/method, business-flow, CORS/CSRF, mixed Node, secure ASP.NET, layered APIM/BFF, material evidence checkpoint, and architecture-neutral event delegation
- File-backed cases: `fixtures/static-public-site/`, `fixtures/client-only-orders-mfe/`, `fixtures/scope-portfolio/`, `fixtures/mixed-node-app/`, `fixtures/secure-dotnet-app/`, and `fixtures/layered-enterprise/`

Run deterministic suite-integrity checks from the skill root:

```bash
python -B evals/run_evals.py
python -B -m unittest discover -s tests -p "test_*.py" -v
```

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

A deterministic pass proves only that the skill contract, source pins, scope-triage controls, selected WSTG IDs, fixtures, and test metadata remain internally consistent. Production-quality claims additionally require model runs, baseline comparison, assertion grading, completion/timing review, and tests against representative application repositories. For the scope-efficiency cases, review transcripts and token counts as well as final answers: passing behavior must avoid recursive exploration of excluded repositories, not merely omit them from the final report.
