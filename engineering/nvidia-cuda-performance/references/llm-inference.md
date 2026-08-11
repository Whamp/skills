# LLM inference gates

Load this reference for CUDA-backed language-model inference. Classify the phase and serving regime before choosing a move.

## Measurement contract

Record:

- model architecture and exact weights;
- dense or MoE structure, active parameters, and routing behavior;
- weight, activation, and KV datatypes and quantization details;
- prompt and generation length distributions;
- concurrency, effective batch, arrival trace, and scheduling policy;
- cold, warm-prefix, and eviction-heavy cache states;
- GPU placement, offload, parallelism, and usable memory;
- runtime, kernel packages, commits/releases, CUDA, build targets, and dispatch;
- output-quality or distribution-equivalence gate.

Measure user outcomes separately:

- **TTFT:** request arrival to first output token;
- **inter-token latency / TPOT:** spacing between generated tokens;
- **prompt throughput:** processed prompt tokens per unit time;
- **output throughput:** generated tokens per unit time;
- **request throughput and SLO attainment;**
- **p50/p95/p99 latency** under a declared arrival trace and adequate request count;
- **capacity:** admitted concurrency, maximum context, and memory headroom.

A handful of aggregate benchmark repetitions can compare throughput but cannot support request-level tail percentiles.

## Phase models

### Prefill

```text
prompt tokens and model dimensions
  -> batched projection and attention work
  -> queueing plus prefill execution
  -> TTFT and interference with decode
```

- **Likely regime:** larger prompt-token batches often produce GEMM-like compute, while attention and memory behavior grow with sequence and implementation.
- **Measure:** admission delay, phase duration, attention and projection kernels, prompt tokens/s, TTFT, memory traffic, and decode delay during concurrent prefills.
- **Candidate gates:** fused exact attention, packed inputs, prefix reuse, chunked prefill, operator fusion, placement, and stable-shape graph capture.
- **Lose-conditions:** unsupported head/mask/datatype shapes, resource-heavy fusion, weak prefix reuse, chunking overhead, or improved prompt throughput with unacceptable TTFT/tails.

### Decode

```text
one next-token step per active sequence
  -> repeated weight and KV access plus small-batch projections
  -> serial target-model steps
  -> inter-token latency and output throughput
```

- **Likely regime:** small effective batches can be weight-traffic, KV-traffic, or launch sensitive; continuous batching can change the projection regime.
- **Measure:** effective batch, per-layer projection and attention time, bytes moved, dequantization/conversion, launch count, graph hits, ITL/TPOT, and output tokens/s.
- **Candidate gates:** weight-only quantization with an efficient selected kernel, KV quantization, continuous batching, CUDA Graphs, fused decode operators, and speculative decoding.
- **Lose-conditions:** conversion erases traffic savings, batch/shape misses the kernel, graph fallbacks dominate, quality crosses its gate, or aggregate throughput harms per-request latency.

### Mixed prefill and decode

```text
compute-heavy prefill and latency-sensitive decode share scheduling/resources
  -> phase interference and queueing
  -> throughput versus TTFT/ITL/tail tradeoff
```

Compare deliberate policies rather than one average utilization number:

- prefill-first and decode-first priorities;
- chunked prefill;
- continuous batching variants;
- separate queues on the same placement;
- physical phase separation only when multi-GPU transfer and capacity gates permit it.

Use the same arrival trace. Measure queueing, phase durations, TTFT, ITL, p95/p99, throughput, and SLO attainment together.

### Long context

Longer context increases KV capacity and attention work, but the exact scaling depends on model architecture, cache representation, fused kernel, batching, and phase.

Sweep context rather than extrapolating one point. Identify:

- the context where a kernel changes or falls back;
- the concurrency where KV capacity limits admission;
- the sequence skew where batching creates tails;
- the depth where KV traffic becomes consequential;
- the point where placement or offload changes.

## Attention and KV mechanisms

### Exact fused attention

- **Mechanism:** avoid materializing the full attention matrix and reduce memory traffic through tiled fusion.
- **Gate:** architecture, head dimension, datatype, mask, sequence shape, and build support the exact path; attention lies on the target phase's critical path.
- **Loses when:** fallback dispatches, resource use is unsuitable for SM86, or attention is not the consequential term.
- **Verify:** selected kernel, materialized/intermediate bytes, attention time, phase time, memory, and end-to-end outcome across context and batch.
- **Boundary:** fused attention does not shrink stored KV state by itself.

### Paged KV management

- **Mechanism:** allocate KV in blocks/pages to reduce fragmentation and support dynamic request growth and sharing.
- **Gate:** allocation waste, growth, or placement constrains concurrency or queueing.
- **Loses when:** metadata/page indirection dominates small workloads or KV bytes per step remain the actual constraint.
- **Verify:** logical versus allocated KV bytes, block utilization, allocation time, admitted concurrency, churn, and tails.
- **Boundary:** paging does not inherently reduce the bytes each attention step reads.

### Prefix reuse

- **Mechanism:** reuse KV blocks for matching prompt prefixes and skip repeated prefill work.
- **Gate:** prefixes repeat, identity is exact, and cache lifetime and capacity permit reuse.
- **Loses when:** hit rate is low, eviction churns, hashing/metadata dominates, or generation dominates the target.
- **Verify:** reused prompt tokens, hit/miss and eviction rates, TTFT by cache state, memory, and throughput.
- **Boundary:** prefix reuse does not accelerate decode after the shared prefix.

### KV quantization

- **Mechanism:** reduce KV storage and traffic.
- **Gate:** runtime and selected kernel support the exact format, scale policy, model shape, and architecture; quality and conversion cost are acceptable.
- **Loses when:** dequantization or format conversion dominates, attention uses a slow fallback, or quality/tails regress.
- **Verify:** storage, bytes read, conversion time, selected kernel, phase time, capacity, and task quality.
- **SM86 boundary:** smaller FP8 storage does not imply native FP8 compute on RTX 3090.

## Weight quantization

Separate four questions:

1. Does the checkpoint fit and load?
2. Does the runtime support the format and model?
3. Which kernel executes for this shape and effective batch?
4. Does reduced traffic beat dequantization and conversion while preserving quality?

### Weight-only low-bit kernels

- **Mechanism:** store fewer weight bits and dequantize into a supported arithmetic path while reusing activations.
- **Gate:** decode or another phase is materially weight-traffic limited; selected architecture-specific kernel supports group size, layout, dimensions, and batch.
- **Loses when:** prefill is compute-bound, repacking/conversion enters steady state, small shapes miss specialization, or quality falls.
- **Verify:** weight bytes, dequantization, Tensor Core and integer issue, selected layout/kernel, kernel time across batches, macro phase time, memory/capacity, and quality.

Do not transfer Marlin, AWQ, GGUF, A10, A100, RTX 4090, or other published results to RTX 3090. Pin the implementation and reproduce the mechanism and outcome.

## CUDA Graphs for inference

- **Mechanism:** reduce repeated host launch work for stable decode or piecewise execution shapes.
- **Gate:** timeline evidence shows launch/submission cost; runtime captures the intended path; shape buckets have high hit rates.
- **Loses when:** graph variants, recapture, unsupported operations, dynamic control flow, or communication dominate.
- **Verify:** graph hit/fallback/recapture rates, launches per output token, host gaps, ITL, throughput, memory, and tails.

A runtime flag or compiled graph support does not prove that requests replay a graph.

## Continuous and chunked batching

- **Mechanism:** increase useful work per iteration, amortize fixed costs, or limit long-prefill interference.
- **Gate:** arrival distribution supplies compatible work and scheduling is a material constraint.
- **Loses when:** queueing and large batches harm TTFT/ITL/tails, shape diversity reduces kernel efficiency, or low load cannot fill batches.
- **Verify:** use a declared arrival trace; sweep batch and chunk policy; report queueing, effective batch, phase kernels, throughput, TTFT, ITL, and tails.

## MoE execution

```text
token routing
  -> variable tokens per expert and placement
  -> grouped/sparse kernels, padding, transfer, and imbalance
  -> stragglers and tail latency
```

Record routed tokens per expert, active experts, load skew, padding or dropped work, expert placement, routed bytes, grouped-kernel shapes, communication, and waits.

Candidates include grouped or sparse kernels, token sorting/compaction, expert placement, expert parallelism, and selective residency. Each loses when small expert batches underfill kernels, routing/compaction dominates, skew creates stragglers, or communication exceeds saved compute.

Model-class support is not evidence of an efficient kernel for its routing pattern.

## Speculative decoding

```text
cheap candidate generation
  + target verification
  -> accepted tokens per expensive target invocation
  -> fewer serial target steps when acceptance economics win
```

- **Gate:** exact runtime/model support; adequate acceptance; draft/head cost, verification shape, memory, and quality fit the workload.
- **Loses when:** acceptance is low, verification is inefficient, draft memory reduces batching, rollback/state semantics fail, or tails worsen.
- **Verify:** accepted tokens per target invocation, acceptance distribution, draft and verify time, rejected work, kernels per output token, graph interaction, ITL, throughput, tails, and distribution/task quality.

Published EAGLE, Medusa, or other speedups are evidence for their named models and systems, not universal speculation gains.

## Placement and offload

Jointly budget weights, KV, runtime workspaces, graph pools, and temporary buffers. More weight residency can leave too little KV capacity; partial offload can introduce transfers that dominate the target phase.

Compare:

- GPU-resident placement where feasible;
- alternative layer or expert placement;
- partial offload;
- one-GPU and multi-GPU layouts;
- memory saved versus admitted context/concurrency and transfer cost.

Record per-device allocations, layer/expert placement, transferred bytes, kernel selection, TTFT, ITL, throughput, tails, and maximum sustainable capacity.

## Runtime support proof

For vLLM, SGLang, TensorRT-LLM, llama.cpp, FlashAttention, FlashInfer, Triton, Marlin, AWQ, or another runtime/kernel:

1. pin release or commit and artifact digest;
2. record CUDA, compiler, build targets, and packaged device code;
3. check model, shape, datatype, quantization, and feature-combination support;
4. complete a representative request;
5. capture runtime dispatch and fallbacks;
6. trace phase and kernel contribution;
7. compare correctness/quality and end-to-end outcomes.

A current README is a discovery lead. It is not a durable compatibility matrix.

## Primary sources

- [FlashAttention-2 paper](https://arxiv.org/abs/2307.08691)
- [FlashAttention at `a369df7`](https://github.com/Dao-AILab/flash-attention/tree/a369df707e1980fb328abcc1733e3457ec10155f)
- [PagedAttention paper](https://arxiv.org/abs/2309.06180)
- [Sarathi-Serve](https://arxiv.org/abs/2403.02310)
- [DistServe](https://arxiv.org/abs/2401.09670)
- [Marlin at `1f25790`](https://github.com/IST-DASLab/marlin/tree/1f25790bdd49fba53106164a24666dade68d7c90)
- [EAGLE](https://arxiv.org/abs/2401.15077)
- [Medusa](https://arxiv.org/abs/2401.10774)
