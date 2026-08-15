# Upstream attribution

This cross-harness Agent Skill is an adaptation inspired by the Mermaid workflow and examples in:

- Project: `pi-mermaid`
- Author: Gurpartap Singh
- Repository: https://github.com/Gurpartap/pi-mermaid
- Upstream revision reviewed: `34cab3ae794422d43707f129120a73ea39f51742`
- License: MIT; preserved in `LICENSE`

The upstream project is a Pi extension that parses Mermaid and renders terminal output. This adaptation does not copy or bundle its executable extension, renderer, runtime dependencies, or Pi-specific APIs. It provides portable instructions for authoring Mermaid source across agent harnesses. Rendering remains the responsibility of the active client.

Local changes should be made directly to this skill and described as changes to the adaptation. When reviewing upstream updates, compare its workflow, supported Mermaid syntax, safety behavior, and examples against this skill; do not describe this skill as a byte-for-byte upstream copy.
