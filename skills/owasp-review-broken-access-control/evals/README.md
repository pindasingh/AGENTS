# Evaluation suite

This directory is development support, not runtime assessment output.

- Skill version: `0.5.1`
- Assessment contract: `1.3`
- Eval suite: `1.5.0`
- Canonical cases: all three OWASP A01:2025 attack scenarios
- Extended cases: false-positive, parser/method, business-flow, CORS/CSRF, mixed Node, secure ASP.NET, layered APIM/BFF, material evidence checkpoint, and architecture-neutral event delegation
- File-backed cases: `fixtures/mixed-node-app/`, `fixtures/secure-dotnet-app/`, and `fixtures/layered-enterprise/`

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

A deterministic pass proves only that the skill contract, source pins, selected WSTG IDs, fixtures, and test metadata remain internally consistent. Production-quality claims additionally require model runs, baseline comparison, assertion grading, completion/timing review, and tests against representative application repositories.
