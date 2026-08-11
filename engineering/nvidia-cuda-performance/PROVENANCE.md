# Provenance and source canon

## Authorship

This skill is an original synthesis by Will Hampson. It reorganizes public technical material into a gate-first process for coding agents. It does not reproduce benchmark tables, implementation code, or substantial prose from any source.

The synthesis adds:

- a six-object causal model connecting application outcomes to work, demand, machine limits, and realized scheduling;
- a gated hypothesis and validation record;
- progressive disclosure between portable CUDA method, NVIDIA mechanisms, SM86/RTX 3090, LLM inference, and multi-GPU work;
- explicit build-versus-dispatch and profiler-versus-outcome proof boundaries;
- source, instance, and empirical-optimum evidence labels.

Host-specific inventory, measurements, and conclusions from private systems are intentionally excluded.

## Research process

The source base was assembled and cross-checked in August 2026 through independent research lanes covering:

1. CUDA causal performance models;
2. optimization technique gates;
3. profiling and validation;
4. GA102/SM86/RTX 3090 specialization;
5. LLM inference;
6. intra-host multi-GPU execution.

The final design received four independent OpenAI-family reviews for source integrity, causal modeling, technique gates, and skill scope. Planned GLM-family reviewers stalled, so the design did not receive cross-family review. This limitation affects review diversity, not source licensing.

## Primary source canon

### NVIDIA architecture and CUDA

- NVIDIA, *NVIDIA Ampere GA102 GPU Architecture Whitepaper*, version 2: <https://www.nvidia.com/content/PDF/nvidia-ampere-ga-102-gpu-architecture-whitepaper-v2.pdf>
- NVIDIA, *Ampere Tuning Guide*, CUDA 11.8 archive: <https://docs.nvidia.com/cuda/archive/11.8.0/ampere-tuning-guide/index.html>
- NVIDIA, *CUDA C++ Programming Guide*: <https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html>
- NVIDIA, *CUDA C++ Best Practices Guide*: <https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html>
- NVIDIA, *CUDA Runtime API*: <https://docs.nvidia.com/cuda/cuda-runtime-api/index.html>
- NVIDIA, *CUDA Binary Utilities*: <https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html>
- NVIDIA, *Compute Sanitizer*: <https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html>

### Profiling and observability

- NVIDIA, *Nsight Systems User Guide*: <https://docs.nvidia.com/nsight-systems/UserGuide/index.html>
- NVIDIA, *Nsight Systems Analysis Guide*: <https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html>
- NVIDIA, *Nsight Compute Profiling Guide*: <https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html>
- NVIDIA, *CUPTI Activity API*: <https://docs.nvidia.com/cupti/api/group__CUPTI__ACTIVITY__API.html>
- NVIDIA, *NVML API*: <https://docs.nvidia.com/deploy/nvml-api/index.html>

Tool behavior is version-sensitive. The skill instructs agents to record the installed version and inspect available profiler sections rather than treating current documentation as a timeless interface.

### Implementations

- NVIDIA CUTLASS at [`86931fef8538008a1a92036732b3eb7fe47b25d0`](https://github.com/NVIDIA/cutlass/tree/86931fef8538008a1a92036732b3eb7fe47b25d0)
- Dao-AILab FlashAttention at [`a369df707e1980fb328abcc1733e3457ec10155f`](https://github.com/Dao-AILab/flash-attention/tree/a369df707e1980fb328abcc1733e3457ec10155f)
- IST-DASLab Marlin at [`1f25790bdd49fba53106164a24666dade68d7c90`](https://github.com/IST-DASLab/marlin/tree/1f25790bdd49fba53106164a24666dade68d7c90)
- NVIDIA CUDA Samples v12.9: <https://github.com/NVIDIA/cuda-samples/tree/v12.9>
- NVIDIA `nccl-tests`, with performance formulas pinned at [`c6eb15875f508076f3f26de4f7da3899701bc4db`](https://github.com/NVIDIA/nccl-tests/blob/c6eb15875f508076f3f26de4f7da3899701bc4db/doc/PERFORMANCE.md)

Repository support statements are treated as version-bound eligibility evidence. They do not establish what a target artifact packaged, dispatched, or measured.

### Research papers

- Tri Dao, *FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning*: <https://arxiv.org/abs/2307.08691>
- Woosuk Kwon et al., *Efficient Memory Management for Large Language Model Serving with PagedAttention*: <https://arxiv.org/abs/2309.06180>
- Amey Agrawal et al., *Sarathi-Serve*: <https://arxiv.org/abs/2403.02310>
- Yinmin Zhong et al., *DistServe*: <https://arxiv.org/abs/2401.09670>
- Yuhui Li et al., *EAGLE*: <https://arxiv.org/abs/2401.15077>
- Tianle Cai et al., *Medusa*: <https://arxiv.org/abs/2401.10774>
- Mohammad Shoeybi et al., *Megatron-LM*: <https://arxiv.org/abs/1909.08053>

Reported speedups remain attached to each paper's hardware, model, workload, and system. The skill uses them as mechanism evidence and experiment leads, never as RTX 3090 predictions.

## Licensing

The original skill text is distributed under the MIT License in [LICENSE](LICENSE). External documentation, papers, and repositories retain their own licenses and copyrights. Links identify sources; they do not incorporate those works into this skill.

This skill is not affiliated with or endorsed by NVIDIA, the cited projects, or their authors.
