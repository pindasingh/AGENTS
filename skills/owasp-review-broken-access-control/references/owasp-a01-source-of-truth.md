# OWASP A01:2025 source of truth

## Purpose and precedence

Use this reference to keep an assessment aligned with OWASP rather than an agent-invented access-control taxonomy. It records the pinned releases used to design the skill; the linked official pages remain normative when live access is available.

Apply sources according to their role:

1. **OWASP Top 10 A01:2025** defines the risk category, common vulnerability examples, prevention guidance, scenarios, and mapped CWEs.
2. **OWASP ASVS 5.0.0 V8** supplies the current testable authorization requirements and assurance levels.
3. **OWASP ASVS 4.0.3 V4** supplies a legacy access-control cross-reference for organizations still using ASVS 4.x identifiers.
4. **OWASP WSTG 4.2 authorization testing** supplies pinned, reproducible testing objectives and techniques; `latest` is supplementary.
5. **OWASP Authorization Cheat Sheet** supplies secure design and implementation guidance.
6. **OWASP API Security Top 10:2023** refines API-specific object, property, function, and business-flow risks.
7. **MITRE CWE pages** define individual weakness identifiers named by OWASP; a CWE mapping does not by itself prove a finding.

Do not present the Top 10 as a complete verification standard. Do not substitute ASVS compliance for an evidence-backed vulnerability review.

## Normative OWASP links

- OWASP Top 10:2025: <https://owasp.org/Top10/2025/>
- A01:2025 Broken Access Control: <https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/>
- OWASP ASVS project and current releases: <https://owasp.org/www-project-application-security-verification-standard/>
- ASVS 5.0.0 V8 Authorization, pinned current source: <https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/en/0x17-V8-Authorization.md>
- ASVS 4.0.3 V4 Access Control, pinned legacy source: <https://github.com/OWASP/ASVS/blob/v4.0.3/4.0/en/0x12-V4-Access-Control.md>
- ASVS 4.x master path supplied by the user (mutable, not used as a version pin): <https://github.com/OWASP/ASVS/blob/master/4.0/en/0x12-V4-Access-Control.md>
- WSTG 4.2 Authorization Testing, pinned stable release: <https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/05-Authorization_Testing/>
- WSTG latest Authorization Testing, supplementary: <https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/README>
- Authorization Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
- API Security Top 10:2023: <https://owasp.org/API-Security/editions/2023/en/0x11-t10/>

Version mappings in a report must include their release, such as `A01:2025`, `ASVS 5.0.0-8.2.2`, `ASVS 4.0.3-4.2.1`, `WSTG v4.2-ATHZ-04`, or `API1:2023`. Avoid ambiguous labels such as “latest OWASP.” Read [asvs-wstg-cheatsheet-crosswalk.md](asvs-wstg-cheatsheet-crosswalk.md) when assigning verification and testing mappings.

## Official A01 common vulnerability examples

The A01:2025 description lists eight bullets. Preserve all eight as explicit coverage branches even where they overlap:

| Branch | Official issue, faithfully summarized |
|---|---|
| `A01-CV-01` | Violation of least privilege or deny by default: access is broadly available rather than granted only to intended capabilities, roles, or users. |
| `A01-CV-02` | Bypass by modifying a URL, parameters, internal application state, HTML, or API requests. |
| `A01-CV-03` | Viewing or editing another account by supplying its identifier—IDOR/object-level authorization failure. |
| `A01-CV-04` | Accessible API operations, particularly POST, PUT, and DELETE, without required access controls. |
| `A01-CV-05` | Privilege elevation: acting without login or gaining privileges beyond those intended for the logged-in user. |
| `A01-CV-06` | Authorization metadata manipulation: replaying or changing JWTs, cookies, hidden fields, or abusing token invalidation. |
| `A01-CV-07` | CORS misconfiguration allowing API access from unauthorized or untrusted origins. |
| `A01-CV-08` | Force browsing to authenticated pages as anonymous or to privileged pages as a standard user. |

The source repeats force browsing as a bypass example and a distinct bullet. Keep both `A01-CV-02` and `A01-CV-08`: the former tests tamperable request/state surfaces broadly; the latter inventories directly reachable protected routes/resources.

## Official A01 prevention and assurance guidance

The A01 page includes a leading statement, nine list items, and a closing testing statement. Preserve all eleven review branches:

| Branch | Official guidance, faithfully summarized |
|---|---|
| `A01-PR-01` | Enforce access control in trusted server-side code or serverless APIs where the attacker cannot modify the check or metadata. |
| `A01-PR-02` | Deny by default except for public resources. |
| `A01-PR-03` | Implement and reuse access-control mechanisms consistently; minimize CORS usage. |
| `A01-PR-04` | Enforce record ownership rather than allowing unrestricted create/read/update/delete of records. |
| `A01-PR-05` | Enforce application-specific business limits in domain models. |
| `A01-PR-06` | Disable directory listing and keep file metadata such as `.git` and backup files outside web roots. |
| `A01-PR-07` | Log access-control failures and alert administrators when appropriate, including repeated failures. |
| `A01-PR-08` | Rate-limit API and controller access to reduce harm from automated attack tooling. |
| `A01-PR-09` | Invalidate stateful sessions after logout; keep stateless JWTs short-lived and use standards-based refresh/revocation for longer-lived access. |
| `A01-PR-10` | Use established toolkits or patterns with simple, declarative access controls. |
| `A01-PR-11` | Include functional access-control unit and integration tests. |

A missing preventive control is not automatically an exploitable finding. Report a vulnerability when it participates in a concrete unauthorized path; otherwise record the branch as a gap or hardening recommendation according to the report contract.

## ASVS 5.0.0 V8 authorization pillars

Use the exact official requirement text from the pinned source when quoting. The relevant structure is:

- **V8.1 Authorization Documentation**
  - 8.1.1 function-level and data-specific rules (L1)
  - 8.1.2 field-level read/write rules, potentially dependent on object state (L2)
  - 8.1.3 documented environmental/contextual security attributes (L3)
  - 8.1.4 documented use of context for allow/challenge/deny/step-up decisions (L3)
- **V8.2 General Authorization Design**
  - 8.2.1 explicit permission for function-level access (L1)
  - 8.2.2 explicit data-item permission to mitigate IDOR/BOLA (L1)
  - 8.2.3 explicit field-level permission to mitigate BOPLA (L2)
  - 8.2.4 contextual controls during session creation and existing sessions (L3)
- **V8.3 Operation Level Authorization**
  - 8.3.1 enforcement at a trusted service layer, not a manipulable client (L1)
  - 8.3.2 prompt application of authorization-value changes or compensating detection/reversion (L3)
  - 8.3.3 decisions based on the originating subject rather than an intermediary's privilege (L3)
- **V8.4 Other Authorization Considerations**
  - 8.4.1 cross-tenant controls (L2)
  - 8.4.2 layered protection for administrative interfaces rather than network location alone (L3)

Do not claim that a vulnerability violates every V8 requirement. Map only requirements whose expected control is contradicted by evidence. State the selected ASVS assessment level separately if the user requests conformance.

## WSTG authorization branches

The pinned WSTG 4.2 Authorization Testing chapter contains the four core procedures below. A01-relevant procedures also exist in information gathering, configuration, identity, session, parser/error handling, business logic, client-side, and API chapters. Use [wstg-v42-a01-selection.md](wstg-v42-a01-selection.md) for the reviewed, deliberately selected set and its applicability rules.

- `WSTG v4.2-ATHZ-01` — directory traversal and file inclusion
- `WSTG v4.2-ATHZ-02` — bypassing authorization schema, including unauthenticated, horizontal, administrative, role, and special-header paths
- `WSTG v4.2-ATHZ-03` — privilege escalation, including role/profile/condition manipulation and vertical bypass
- `WSTG v4.2-ATHZ-04` — insecure direct object references in records, operations, files, and functionality

The latest WSTG additionally separates OAuth authorization-server and client testing under `WSTG-ATHZ-05.1` and `WSTG-ATHZ-05.2`. Treat those as supplementary latest-version mappings, not WSTG 4.2 identifiers. OAuth tests apply only when the corresponding OAuth role and flow are in scope. Authentication and token-validation defects may map primarily to A07; include them in A01 only when they cause or enable an authorization decision failure.

## API Security Top 10:2023 cross-references

When APIs are present, use these refinements:

- `API1:2023 Broken Object Level Authorization` — caller-controlled object IDs and missing per-object authorization; official mappings include CWE-285 and CWE-639.
- `API3:2023 Broken Object Property Level Authorization` — unauthorized field reads/writes, including excessive exposure and mass assignment; official mappings include CWE-213 and CWE-915.
- `API5:2023 Broken Function Level Authorization` — access to administrative or otherwise privileged functions; official mapping includes CWE-285.
- `API6:2023 Unrestricted Access to Sensitive Business Flows` — automated abuse of legitimate high-value flows and business limits.

API3 includes CWEs not in the A01:2025 list. It is still a useful precise API mapping when field-level authorization is the observed issue.

## All 40 CWEs mapped by A01:2025

The official A01 page maps these 40 CWEs. The review playbook groups them into practical branches so every identifier is considered without applying every identifier to every finding.

| CWE | Official name shown by A01:2025 |
|---|---|
| CWE-22 | Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal') |
| CWE-23 | Relative Path Traversal |
| CWE-36 | Absolute Path Traversal |
| CWE-59 | Improper Link Resolution Before File Access ('Link Following') |
| CWE-61 | UNIX Symbolic Link (Symlink) Following |
| CWE-65 | Windows Hard Link |
| CWE-200 | Exposure of Sensitive Information to an Unauthorized Actor |
| CWE-201 | Exposure of Sensitive Information Through Sent Data |
| CWE-219 | Storage of File with Sensitive Data Under Web Root |
| CWE-276 | Incorrect Default Permissions |
| CWE-281 | Improper Preservation of Permissions |
| CWE-282 | Improper Ownership Management |
| CWE-283 | Unverified Ownership |
| CWE-284 | Improper Access Control |
| CWE-285 | Improper Authorization |
| CWE-352 | Cross-Site Request Forgery (CSRF) |
| CWE-359 | Exposure of Private Personal Information to an Unauthorized Actor |
| CWE-377 | Insecure Temporary File |
| CWE-379 | Creation of Temporary File in Directory with Insecure Permissions |
| CWE-402 | Transmission of Private Resources into a New Sphere ('Resource Leak') |
| CWE-424 | Improper Protection of Alternate Path |
| CWE-425 | Direct Request ('Forced Browsing') |
| CWE-441 | Unintended Proxy or Intermediary ('Confused Deputy') |
| CWE-497 | Exposure of Sensitive System Information to an Unauthorized Control Sphere |
| CWE-538 | Insertion of Sensitive Information into Externally-Accessible File or Directory |
| CWE-540 | Inclusion of Sensitive Information in Source Code |
| CWE-548 | Exposure of Information Through Directory Listing |
| CWE-552 | Files or Directories Accessible to External Parties |
| CWE-566 | Authorization Bypass Through User-Controlled SQL Primary Key |
| CWE-601 | URL Redirection to Untrusted Site ('Open Redirect') |
| CWE-615 | Inclusion of Sensitive Information in Source Code Comments |
| CWE-639 | Authorization Bypass Through User-Controlled Key |
| CWE-668 | Exposure of Resource to Wrong Sphere |
| CWE-732 | Incorrect Permission Assignment for Critical Resource |
| CWE-749 | Exposed Dangerous Method or Function |
| CWE-862 | Missing Authorization |
| CWE-863 | Incorrect Authorization |
| CWE-918 | Server-Side Request Forgery (SSRF) |
| CWE-922 | Insecure Storage of Sensitive Information |
| CWE-1275 | Sensitive Cookie with Improper SameSite Attribute |

Broad mappings such as CWE-284, CWE-285, CWE-862, and CWE-863 should not displace a more specific supported mapping. Findings about path traversal, CSRF, SSRF, open redirect, or sensitive source files must still demonstrate an access-control or resource-sphere consequence to be reported under this A01-focused review.
