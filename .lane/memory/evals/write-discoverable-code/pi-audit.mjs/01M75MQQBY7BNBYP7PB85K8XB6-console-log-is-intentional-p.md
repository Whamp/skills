---
id: 01M75MQQBY7BNBYP7PB85K8XB6
anchor: '@file'
created: 2026-11-11T15:48:29Z
norm: '1'
sig: e3b0c44298fc1c14
body_hash: 922f66fa4f902576
raw_hash: 530f5d0944298798
lines: 1-38
---

console.log is intentional protocol output: Pi routes extension logs to stderr, and preflight/collection require the eval_profile JSON record. Removing it breaks the context-verification gate.
