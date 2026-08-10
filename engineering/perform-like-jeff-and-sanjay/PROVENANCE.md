# Provenance and source coverage

## Source

This skill is an original synthesis and adaptation of:

- Jeffrey Dean and Sanjay Ghemawat, *Performance Hints* (2025)
- Official publication: <https://abseil.io/fast/hints.html>
- Source repository: <https://github.com/abseil/abseil.github.io>
- Source revision: [`e9e24835cb889fe25251cb9ec6d51b79233e358d`](https://github.com/abseil/abseil.github.io/commit/e9e24835cb889fe25251cb9ec6d51b79233e358d)
- Source license: Apache License 2.0

The adaptation reorganizes the article into an agent-executable process, generalizes mechanisms beyond C++ and Google systems, adds explicit gates and lose-conditions, and separates conditional C++/protobuf material. It does not reproduce the source's code examples or benchmark tables.

This skill is not affiliated with or endorsed by Jeffrey Dean, Sanjay Ghemawat, Google, Abseil, or the acknowledged reviewers. Names and project marks identify the source only.

## License

This skill is distributed under the Apache License 2.0. The full text is in [LICENSE](LICENSE). The source repository did not provide a separate `NOTICE` file at the cited revision.

## Heading coverage

Every source chapter informed the adaptation:

| Source heading | Adapted location |
| --- | --- |
| Preamble; importance of thinking about performance | `SKILL.md` scope, design-time rule, and gated-move discipline |
| Estimation | `SKILL.md` Steps 1–2 |
| Measurement; flat profiles | `SKILL.md` Step 3 |
| API considerations | `SKILL.md` Steps 4–5 and `references/technique-gates.md` API gates |
| Algorithmic improvements | `references/technique-gates.md` algorithm and whole-input gates |
| Better memory representation | `references/technique-gates.md` representation and locality gates |
| Reduce allocations | `references/technique-gates.md` lifecycle, arenas, copying, and reuse gates |
| Avoid unnecessary work | `references/technique-gates.md` avoid-work gates |
| Code size considerations | `references/technique-gates.md` static-code gates and C++ conditional reference |
| Parallelization and synchronization | `references/technique-gates.md` concurrency and coordination gates |
| Protocol Buffer advice | `references/cpp-and-protobuf-gates.md` protobuf branch |
| C++-specific advice | `references/cpp-and-protobuf-gates.md` C++ branch |
| Bulk operations | `references/technique-gates.md` whole-input and bulk-instruction gates |
| CLs demonstrating multiple techniques | `SKILL.md` Steps 6–8: attribution, micro/macro validation, regressions, and evidence bounds |
| Further reading | Source basis recorded here; the external bibliography was not needed to execute the skill |
| Suggested citation | Source citation above |
| Acknowledgments | Feedback contributors retained below without implying authorship or endorsement |

## Source acknowledgments

The source acknowledges feedback from Adrian Ulrich, Alexander Kuzmin, Alexei Bendebury, Alexey Alexandrov, Amer Diwan, Austin Sims, Benoit Boissinot, Brooks Moses, Chris Kennelly, Chris Ruemmler, Danila Kutenin, Darryl Gove, David Majnemer, Dmitry Vyukov, Emanuel Taropa, Felix Broberg, Francis Birck Moreira, Gideon Glass, Henrik Stewenius, Jeremy Dorfman, John Dethridge, Kurt Kluever, Kyle Konrad, Lucas Pereira, Marc Eaddy, Michael Marty, Michael Whittaker, Mircea Trofin, Misha Brukman, Nicolas Hillegeer, Ranjit Mathew, Rasmus Larsen, Soheil Hassas Yeganeh, Srdjan Petrovic, Steinar H. Gunderson, Stergios Stergiou, Steven Timotius, Sylvain Vignaud, Thomas Etter, Thomas Köppe, Tim Chestnutt, Todd Lipcon, Vance Lankhaar, Victor Costan, Yao Zuo, Zhou Fang, and Zuguang Yang. They are not represented as authors or endorsers of this skill.
