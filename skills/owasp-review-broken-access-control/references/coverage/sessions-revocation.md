# Sessions, tokens, stale authority, and revocation

Load this file only when selected authorization paths depend on sessions, cookies, JWT/OAuth/OIDC tokens, signed links, cached decisions, role/tenant/ownership changes, logout, disablement, or long-lived connections.

## Authority semantics

For every credential or cached decision determine:

- represented subject and actor/delegation chain;
- issuer and integrity validation;
- audience, scope, role/group, tenant, resource, and action binding;
- issuance, lifetime, refresh, rotation, and revocation behavior;
- how password, role, tenant, ownership, employment, or account-state changes take effect;
- whether downstream tiers preserve the authority needed for the selected resource.

A valid token proves only the identity/authority it was designed to represent. A readable JWT is not a vulnerability, and token validity does not replace object, field, function, tenant, or state authorization.

## Selected checks

Inspect logout and server-side session invalidation; stateless access-token lifetime and refresh-token reuse controls; disabled users; stale roles/scopes/groups; tenant or ownership transfer; signing-key rollover; decision caches; websocket/stream lifetime; queued/delayed operations; signed-link audience/resource/expiry binding; and failure behavior when revocation or policy services are unavailable.

Check caller-controlled cookies, headers, claims, hidden fields, token exchange inputs, and trusted proxy assertions only when they affect a selected protected operation. Establish who can alter the input and how the trusted decision consumes it.

## Evidence and tests

A stale-authority finding requires a protected operation that remains available beyond the intended change window, not merely a missing logout call. Propose allowed current-authority and denied revoked/stale-authority cases, asserting no sensitive response or side effect.

Relevant coverage includes A01-CV-06 and A01-PR-09, with A01-PR-11 for tests. Use CWE-352 only for supported CSRF paths and another precise CWE when evidence warrants it. Load `browser-cors-csrf.md` only for browser cross-origin/request-forgery behavior and `../asvs-wstg-cheatsheet-crosswalk.md` only when mappings are requested.
