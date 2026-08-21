# Design provenance

This skill and the matching Pi extension were redesigned from the transparent handoff pattern demonstrated by Mario Zechner (`badlogic`):

- Gist: https://gist.github.com/badlogic/d36e325248b68414e1c6528c6ed6b525
- Revision reviewed: `3d7d74a92bef0ff41827df1db3a0f49e0f5b1e4b`

The upstream gist launches Pi through tmux, writes the complete task to a prompt file, and reads the durable assistant result from JSONL. The referenced screenshot shows a higher-level `subagent spawn --name ... --tools ... --no-skills --prompt ...` wrapper.

This repository preserves the important contract—visible run name, explicit tools, disabled skills, complete prompt, isolated Pi process—while retaining its existing background completion hand-back and context viewer. It does not copy the gist's tmux/wait implementation or claim exact CLI compatibility.
