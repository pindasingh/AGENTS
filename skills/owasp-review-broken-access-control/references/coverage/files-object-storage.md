# Files, object storage, static resources, and exposed artifacts

Load this file only when selected deployment/runtime evidence includes protected files, static handlers, upload/download paths, object stores, CDNs, signed links, caches, web roots, directory indexes, archives, backups, or generated deployment copies. Do not hunt through a public static repository for hypothetical sensitive files when triage found no protected resource or deployment path.

## Trace publication and access

Identify the protected file/object, intended audience, action, authoritative identity, path/key inputs, origin/edge policy, cache behavior, and direct-origin reachability. Inspect:

- download/upload/list/delete operations and owner/tenant scope;
- path normalization, traversal, aliases, symlinks, filenames, and storage keys;
- bucket/container/object IAM or ACL defaults and inherited policy;
- signed URL resource, audience, method, expiry, and revocation binding;
- CDN/cache keys and principal/tenant variance;
- origin bypass, direct object URLs, metadata, versions, and backups;
- directory listing and build/deployment copy rules;
- source maps, `.git`, archives, editor backups, environment files, logs, temporary files, and generated reports only when deployment evidence can expose them.

Separate intentional public publication from missing authorization. Repository presence does not establish runtime exposure.

## Evidence and tests

A finding needs a reachable protected artifact and an unauthorized read/write/list/delete path. Use exact deployment/configuration and handler evidence; mark deployed-state assumptions as gaps. Test intended access plus peer, cross-tenant, anonymous, expired-link, alternate-path, direct-origin, and cache-isolation cases as applicable.

Relevant coverage includes A01-CV-01/A01-CV-02/A01-CV-03/A01-CV-08, A01-PR-02/A01-PR-04/A01-PR-06/A01-PR-11, and precise path/file/exposure CWEs supported by `comprehensive.md`. Load `sessions-revocation.md` for signed-link lifetime/revocation and `gateways-delegation.md` when edge/origin identity changes are material.
