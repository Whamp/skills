# Multi-GPU gates

Load this reference for intra-host CUDA P2P, NCCL, or multi-GPU placement. Treat scaling as a topology-and-workload experiment, not a GPU-count assumption.

## Target evidence packet

Record stable GPU UUIDs and PCI bus IDs, then collect:

- GPU model, compute capability, memory, power limit, and usable memory;
- current and maximum PCIe generation and width under relevant load;
- GPU-to-NUMA placement and CPU/worker affinity;
- every directed CUDA P2P capability pair;
- pairwise transfer integrity, latency, and bandwidth;
- optional physical-link topology as a separate measured configuration;
- BAR1 and IOMMU state when they bear on the proposed mechanism;
- driver, CUDA, NCCL, runtime, build, environment variables, and rank/device order;
- clocks, temperature, power, performance state, and throttle reasons during sustained runs.

Preserve raw topology and tool output with the experiment record. Do not infer negotiated links or transport from product names.

## Pairwise proof

For every ordered pair `(source, destination)`:

1. query CUDA peer-access capability;
2. enable the intended path where supported;
3. verify directed transfer contents and completion;
4. measure latency and uni/bidirectional bandwidth across relevant sizes;
5. repeat under representative concurrency and load;
6. record fallback behavior.

Capability is not performance. A topology label is a hypothesis until directed measurements cluster as predicted.

GPUDirect RDMA describes GPU interaction with third-party PCIe peers. Do not apply its NIC/storage BAR and IOMMU rules mechanically to ordinary GPU-to-GPU CUDA P2P.

## Fair baselines

Hold model or kernel, precision, software, workload, warmup, measurement window, correctness, CPU placement, power, and thermal starting conditions constant.

Compare every applicable layout:

1. best one-GPU execution when it fits;
2. independent one-GPU replicas;
3. best two-GPU coupled execution;
4. two replicas of a two-GPU layout;
5. independent four-GPU replicas;
6. four-GPU coupled execution;
7. relevant uneven or hybrid placements.

Report latency, throughput, memory/capacity, correctness, and sustained behavior. Aggregate throughput does not establish scaling when batching, request latency, quality, or memory policy changed.

## Causal scaling model

For a transfer payload `S`, use this as a fit, not a guarantee:

```text
communication time(S) ~= fixed latency + S / achieved bandwidth
```

For the application:

```text
multi-GPU time
  ~= partitioned compute
   + exposed communication
   + imbalance
   + synchronization
   + host/runtime overhead
```

The move wins only when the compute or capacity benefit exceeds the added terms on the declared target path.

NCCL `algbw` and `busbw` are benchmark-defined metrics. Use them consistently to compare collective runs; neither is a direct physical-link counter.

## Strategy gates

### Replication

- **Mechanism:** serve or compute independent work without per-request cross-GPU coupling.
- **Gate:** the workload fits one GPU and requests or partitions are independent.
- **Loses when:** one request needs more memory/latency than one GPU provides or load balancing is poor.
- **Verify:** use replication as the lowest-coupling throughput baseline for every coupled strategy.

### Tensor parallelism

- **Mechanism:** split intra-layer operations and combine partial results through repeated collectives.
- **Gate:** one-device memory or latency requires the split; collective cost can be hidden or is smaller than compute saved.
- **Loses when:** small-batch or PCIe collectives dominate, synchronization repeats each layer, or rank imbalance grows.
- **Verify:** measure collective payload and frequency, exposed communication, per-rank compute, waits, memory, and target latency/throughput.

### Pipeline or layer placement

- **Mechanism:** place contiguous stages or layers on devices and pass activations between fewer boundaries.
- **Gate:** stage memory fits, transfer frequency is lower than tensor-parallel collectives, and enough work exists to fill the pipeline.
- **Loses when:** pipeline bubbles, activation transfer, latency, or one slow stage dominates.
- **Verify:** measure per-stage time and memory, boundaries, activation bytes, bubbles, microbatch policy, and end-to-end tails. Balance time, not layer count.

### Expert parallelism

- **Mechanism:** place experts across devices and route tokens to their owners.
- **Gate:** expert memory or grouped execution benefits exceed routed communication and imbalance.
- **Loses when:** token counts are small or skewed, all-to-all traffic dominates, or stragglers set step time.
- **Verify:** record tokens and bytes per expert/rank, grouped-kernel shapes, collective/transfer time, imbalance, waits, and tails.

### Prefill/decode separation

- **Mechanism:** isolate compute-heavy prefill from latency-sensitive decode and tune their resources independently.
- **Gate:** phase interference is measured; each phase can use its assigned capacity; KV transfer and queueing cost fit the SLO.
- **Loses when:** KV transfer, queueing, low utilization, or phase imbalance exceeds the isolation benefit.
- **Verify:** compare colocated scheduling, separate queues without physical separation, and physical phase placement where supported. Measure KV bytes, transfer latency, TTFT, ITL, tails, throughput, and SLO attainment.

### Uneven placement

- **Mechanism:** assign work according to measured compute, memory, and link differences rather than equal counts.
- **Gate:** devices, links, layers, experts, or phase work are materially asymmetric.
- **Loses when:** placement adds routing complexity without reducing the slowest stage or exposed communication.
- **Verify:** sweep plausible placements and rank orders; measure each device's compute, memory, communication, wait, and sustained clocks.

## NCCL gates

Pin the NCCL version. API availability, registration, transport controls, collective implementations, and graph behavior change across releases.

For the target version:

- run `nccl-tests` correctness and performance across small and large messages;
- choose the collective that matches the dataflow instead of expressing every exchange as AllReduce;
- capture selected transport and topology evidence when available;
- test rank order and process/thread organization;
- trace collectives in the application, not only in isolation;
- treat environment variables as diagnostic experiments with explicit scope and rollback.

Healthy `nccl-tests` with poor application scaling points away from raw collective bandwidth and toward frequency, exposed placement, imbalance, synchronization, or host/runtime overhead. Poor `nccl-tests` does not by itself prove the application is communication-bound.

## Overlap and synchronization

Timeline concurrency is not net benefit. Accept an overlap claim only when:

1. operations are independent under explicit stream and memory-order contracts;
2. the timeline shows the intended concurrence;
3. exposed communication or waiting falls;
4. unprofiled wall time improves;
5. correctness holds across message sizes, streams, ranks, and device orderings.

Overlapping two operations that compete for the same resource can lengthen the critical path.

## RTX 3090 boundary

RTX 3090's optional NVLink capability is a two-card board configuration, not a general four-GPU fabric. Treat any physically linked pair as one separately measured topology. Do not prescribe acquiring or using NVLink; compare the available host configurations with the same pairwise, collective, application, correctness, and sustained-behavior gates.

Native P2P access, native atomics, CUDA copies, NCCL transport, and application communication are different capabilities. Verify each one required by the proposed design.

## Correctness and sustained validation

Run:

- directed transfer integrity checks;
- collective correctness across sizes, in-place/out-of-place cases, ranks, and streams used;
- application output or quality comparison across GPU counts and rank orderings;
- stress and soak runs that can expose ordering, timeout, or memory faults;
- sustained power, temperature, clocks, and throttle sampling;
- failure and restart behavior where the service contract requires it.

A short benchmark taken at different clocks or thermal states is confounded.

## Lose-conditions

Reject or simplify the design when:

- the workload fits one GPU and coupled execution loses to replication;
- four GPUs do not beat the best one- or two-GPU layout on the declared metric;
- communication exceeds compute saved;
- placement cannot avoid weak or asymmetric pairs;
- load imbalance or synchronization sets step time;
- claimed overlap does not reduce exposed time;
- gains disappear under sustained power or thermal behavior;
- correctness changes with GPU count, rank order, streams, or P2P settings;
- the result relies on unstable device indices or unreproducible transport assumptions.

## Primary sources

- [CUDA Runtime peer-device API](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__PEER.html)
- [CUDA sample `p2pBandwidthLatencyTest` at v12.9](https://github.com/NVIDIA/cuda-samples/tree/v12.9/Samples/5_Domain_Specific/p2pBandwidthLatencyTest)
- [NVIDIA `nccl-tests`](https://github.com/NVIDIA/nccl-tests)
- [`nccl-tests` performance guide at `c6eb158`](https://github.com/NVIDIA/nccl-tests/blob/c6eb15875f508076f3f26de4f7da3899701bc4db/doc/PERFORMANCE.md)
- [NCCL 2.30.7 overview](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/overview.html)
- [NCCL 2.30.7 group calls](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/groups.html)
- [NCCL environment variables](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html)
- [Megatron-LM](https://arxiv.org/abs/1909.08053)
- [DistServe](https://arxiv.org/abs/2401.09670)
