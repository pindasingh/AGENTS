# Browser trust boundaries: CORS and CSRF

Load this file only when a selected path uses a browser with cookies, browser-managed credentials, or cross-origin response access. Do not load it for a public static site, non-browser service, or token API merely because the repository contains frontend code.

## Keep the boundaries separate

- **CORS** controls whether browser script from another origin may read a response.
- **CSRF** concerns a third-party site causing a victim browser to perform an authenticated state-changing action.
- **Server authorization** still decides whether the represented actor may perform the action on the resource.

A wildcard on intentionally public non-credentialed content is not broken access control. POST alone is not CSRF protection, and CORS is not CSRF protection.

## CORS review

For protected browser responses inspect exact allowed origins, reflection, wildcard behavior, credentials, `null` origins, subdomain matching, methods/headers, preflight, `Vary: Origin`, caches, and environment overrides. Establish browser behavior, credential mode, protected response content, and a malicious origin capable of reading it before reporting a finding.

## CSRF review

For state changes inspect cookie/session authentication, SameSite behavior, request method and content type, simple-request feasibility, anti-forgery tokens, Origin/Referer validation, custom-header/preflight assumptions, login/logout behavior, and side effects. State the victim identity, attacker-controlled action/resource values, expected rejection, and evidenced acceptance path.

## Evidence and tests

Use synthetic accounts and origins in an authorized environment. Keep tests separate:

- malicious-origin protected-response read for CORS;
- unwanted victim-authorized state change for CSRF;
- direct server authorization checks for owner/tenant/role boundaries.

Map only supported issues: A01-CV-07 and CWE-1275 for a concrete CORS trust failure; A01-CV-06/A01-PR-09 and CWE-352 for supported CSRF/session authority paths; A01-PR-03 for centralized minimal CORS. Load `../wstg-v42-a01-selection.md` only when detailed WSTG procedures are requested.
