# A01 verification and testing crosswalk

## Purpose

Use this crosswalk after identifying an evidence-backed A01 issue. It prevents three common mistakes:

1. citing a mutable or unversioned source;
2. treating old and current ASVS identifiers as interchangeable;
3. mapping every available control to a finding instead of selecting the controls contradicted by evidence.

Primary reproducible sources:

- [ASVS 5.0.0 V8 Authorization](https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/en/0x17-V8-Authorization.md)
- [ASVS 4.0.3 V4 Access Control](https://github.com/OWASP/ASVS/blob/v4.0.3/4.0/en/0x12-V4-Access-Control.md)
- [WSTG 4.2 Authorization Testing](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/05-Authorization_Testing/)
- [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

ASVS 5.0.0 is the current primary verification source. Include ASVS 4.0.3 identifiers only when the user requests a 4.x report, an existing control catalogue uses them, or a migration crosswalk is useful. Never write `ASVS V4/V8` without the release number.

## ASVS 4.0.3 V4 to ASVS 5.0.0 crosswalk

This is a semantic aid, not an official one-to-one migration table. ASVS 5 reorganized and refined authorization; some 4.0.3 controls moved outside V8 or split into several requirements.

| ASVS 4.0.3 | Intent | Closest ASVS 5.0.0 requirement(s) | Notes |
|---|---|---|---|
| 4.1.1 | Trusted service-layer enforcement | 8.3.1 | Strong direct correspondence. |
| 4.1.2 | Prevent manipulation of authorization attributes and policy data | 8.3.2; 8.3.3 where delegated identity is involved | 5.0 emphasizes immediate changes and originating-subject authority; token integrity also intersects V9/V10. |
| 4.1.3 | Least privilege for functions, data, files, URLs, controllers, and services | 8.2.1, 8.2.2, 8.2.3 | 5.0 separates function-, data-, and field-level authorization. |
| 4.1.5 | Fail securely when exceptions occur | No direct V8 equivalent | Assess fail-closed behavior; ASVS 5.0 exception/error handling also intersects V16. Do not drop this check merely because it moved. |
| 4.2.1 | Protect CRUD operations from IDOR | 8.2.2; 8.4.1 for tenants | 5.0 explicitly names IDOR/BOLA and adds cross-tenant controls. |
| 4.2.2 | Anti-CSRF and anti-automation | 3.3.2, 3.5.1, 3.5.2; business-limit controls may intersect V2 | This control moved outside V8 in 5.0. CORS and CSRF are related browser boundaries but are not interchangeable. |
| 4.3.1 | MFA for administrative interfaces | 8.4.2 plus applicable V6 authentication requirements | 5.0 calls for layered, contextual administrative protection rather than treating MFA as the only authorization control. |
| 4.3.2 | Disable directory browsing and metadata disclosure | Applicable V13/V14 deployment and data-protection controls; no direct V8 equivalent | Remains explicit A01:2025 prevention guidance and WSTG-ATHZ-01 coverage. |
| 4.3.3 | Step-up/adaptive authorization and segregation of duties | 8.1.3, 8.1.4, 8.2.4, 8.4.2 | 5.0 makes context documentation and adaptive decisions more explicit. |

ASVS 4.0.3 requirement 4.1.4 is marked deleted as a duplicate of 4.1.3 and must not be cited as an active requirement.

## WSTG 4.2 test selection

Use the stable identifier with release context in reports:

| Identifier | Use when | Typical evidence/result |
|---|---|---|
| `WSTG v4.2-ATHZ-01` | Paths, files, directories, links, archives, or include behavior may escape the intended resource boundary | A controlled path reaches a file outside authorized scope, or deployment/source evidence proves that path resolution is unconstrained. |
| `WSTG v4.2-ATHZ-02` | Anonymous, horizontal, administrative, role, alternate-path/method, or trusted-header bypass is plausible | A lower-privilege subject reaches a protected operation through a missing or inconsistent enforcement path. |
| `WSTG v4.2-ATHZ-03` | Role, profile, condition, tenant, group, or vertical privilege can be manipulated | A subject obtains a function or action outside its intended privileges. |
| `WSTG v4.2-ATHZ-04` | A caller controls an object/record/file/function identifier | A peer or cross-tenant subject can read, change, delete, or invoke a resource without data-specific permission. |

WSTG procedures support test design; they do not set finding severity and do not prove that a source pattern is exploitable.

## Authorization Cheat Sheet review controls

The Authorization Cheat Sheet supplies design and implementation guidance. Use its recommendations as review questions:

| Cheat Sheet recommendation | Review question | A01 branches |
|---|---|---|
| Enforce least privilege | Does each actor have only the functions, records, fields, and contexts explicitly needed? | CV-01, CV-05, PR-04 |
| Deny by default | What happens to new, unmatched, failed, or exceptional paths? Which resources are explicitly public? | CV-01, PR-02 |
| Validate permissions on every request | Do alternate methods, versions, routes, batch operations, and direct backend paths invoke the same policy? | CV-02, CV-04, CV-08, PR-03 |
| Review framework/tool semantics | Are defaults, annotations, inheritance, proxies, middleware order, and custom checks understood and tested? | PR-03, PR-10 |
| Prefer attribute- and relationship-aware decisions where appropriate | Does authorization account for ownership, tenant, relationship, state, and context rather than relying only on coarse roles? | CV-03, CV-05, PR-04, PR-05 |
| Protect lookup identifiers with authorization | Is every caller-controlled key constrained by the originating subject's authorized scope? | CV-03, PR-04 |
| Protect static resources | Are files, archives, source maps, metadata, and direct download paths subject to intended policy? | CV-08, PR-06 |
| Enforce checks at the correct trusted location | Can clients, gateways, intermediaries, or caller-supplied metadata bypass the authoritative decision? | CV-02, CV-06, PR-01 |
| Exit safely when checks fail | Do exceptions, policy-service outages, malformed claims, and ambiguous decisions deny without leaking data or causing side effects? | CV-01, PR-02 |
| Log access-control events | Are denials and suspicious repetitions attributable and actionable without leaking sensitive data? | PR-07 |
| Add unit and integration tests | Do tests cover allowed and anonymous, peer, lower-role, cross-tenant, alternate-path, revoked, and business-limit denials? | PR-11 |

Cheat Sheet nonconformance alone is normally a control gap or remediation input. Elevate it to a vulnerability finding only when the assessment establishes an unauthorized path and impact.

## Branch-to-source quick map

| A01 branch | ASVS 5.0.0 | ASVS 4.0.3 | WSTG 4.2 | Cheat Sheet emphasis |
|---|---|---|---|---|
| A01-CV-01 | 8.2.1–8.2.3 | 4.1.3, 4.1.5 | ATHZ-02, ATHZ-03 | least privilege; deny default; safe failure |
| A01-CV-02 | 8.3.1 | 4.1.1, 4.1.2, 4.1.5 | ATHZ-02 | every request; correct location |
| A01-CV-03 | 8.2.2, 8.4.1 | 4.2.1 | ATHZ-04 | lookup IDs; attributes/relationships |
| A01-CV-04 | 8.2.1–8.2.3 | 4.1.3, 4.2.1 | ATHZ-02, ATHZ-03 | every request |
| A01-CV-05 | 8.2.1, 8.2.4, 8.4.2 | 4.1.3, 4.3.1, 4.3.3 | ATHZ-03 | least privilege |
| A01-CV-06 | 8.3.2, 8.3.3 | 4.1.2 | ATHZ-02 where it creates bypass | correct location; safe failure |
| A01-CV-07 | 3.3.2, 3.4.2, 3.5.1, 3.5.2 | 4.2.2 | ATHZ-02 where protected access results | every request |
| A01-CV-08 | 8.2.1, 8.3.1 | 4.1.1, 4.1.3 | ATHZ-02, ATHZ-03 | static resources; every request |
| A01-PR-01 | 8.3.1, 8.3.3 | 4.1.1 | ATHZ-02 | correct location |
| A01-PR-02 | 8.2.1–8.2.3 | 4.1.3, 4.1.5 | ATHZ-02 | deny default; safe failure |
| A01-PR-03 | 8.3.1 | 4.1.1 | ATHZ-02 | framework review; every request |
| A01-PR-04 | 8.2.2, 8.4.1 | 4.2.1 | ATHZ-04 | lookup IDs; attributes/relationships |
| A01-PR-05 | 8.1.2–8.1.4, 8.2.3–8.2.4 | 4.3.3 | ATHZ-03 where privilege/state applies | attributes/relationships |
| A01-PR-06 | adjacent V13/V14 controls | 4.3.2 | ATHZ-01, ATHZ-02 | static resources |
| A01-PR-07 | adjacent V16 controls | no direct V4 control | test denial observability alongside ATHZ checks | logging |
| A01-PR-08 | adjacent V2 controls | 4.2.2 | repeat only within authorized safe scope | business-rule enforcement |
| A01-PR-09 | 8.3.2 | 4.1.2 | ATHZ-02/03 with revoked authority | every request; safe failure |
| A01-PR-10 | 8.3.1 | 4.1.1 | all applicable ATHZ procedures | framework review |
| A01-PR-11 | all selected requirements | all selected requirements | all selected procedures | unit and integration tests |

Prefix WSTG report mappings with the pinned release (`WSTG v4.2-ATHZ-04`). For ASVS 5 requirements outside V8, explain why the adjacent control is relevant to the A01 finding.
