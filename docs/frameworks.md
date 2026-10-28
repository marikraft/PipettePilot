# Connecting LLMs to lab equipment: options compared

This project uses **direct tool calling** on the LLM side and **PyLabRobot** on the lab side, with validation kept outside the model. This page lays out the alternatives and why they weren't chosen for a first proof of concept.

The question has two layers:

1. **LLM side:** how a model's intent turns into a call that software can act on.
2. **Lab side:** how that call reaches an instrument.

## LLM side

| Approach | How it works | Strengths | Risks in a regulated lab |
|---|---|---|---|
| **Code generation** | The model writes a protocol script (e.g. Python against a robot API) that is then executed. Coscientist (Boiko et al., *Nature* 2023) showed LLMs reading hardware documentation and driving liquid handlers this way. | Most expressive: loops, conditionals, any API call. | The output is arbitrary code. Checking it before it runs means analysing a program, not a list of actions, and executing model-written code is a security concern in itself. |
| **Direct tool calling** *(used here)* | The model picks from a fixed set of functions (`transfer`, `distribute`, `ask_clarification`, `refuse`) and fills in typed arguments. | The output is data, not code: easy to validate, log and show to a human. Asking and refusing are first-class answers. | Limited to the tools provided; new workflows need new tools. Tool definitions are written for one provider's API. |
| **Model Context Protocol (MCP)** | An open standard for exposing tools to any MCP-compatible client or model. The same tool calls, served by a separate process. Early lab examples exist, such as `labmcp` for balances and hotplates. | Write the instrument interface once, use it from any model or app. Separates "what the lab exposes" from "which model uses it". | Same safety needs as tool calling, plus a server to deploy and secure. Doesn't validate anything by itself. |
| **Agent frameworks** (LangChain, LangGraph and similar) | Orchestration layers for multi-step loops: the model acts, sees the result, decides the next step. | Useful once there are many tools, retrieval or long multi-step tasks. | A model that acts step by step, reacting to results, is much harder to validate before the first movement. More abstraction between you and what the model actually did. |

## Lab side

| Option | What it is | Notes |
|---|---|---|
| **PyLabRobot** *(used here)* | Open-source Python interface with one set of commands across Hamilton STAR/STARlet, Tecan Freedom EVO and Opentrons OT-2, plus a simulator (Wierenga et al., 2023). | Hardware-agnostic and runs without a robot. Less mature than vendor software for validated production methods. |
| **Vendor Python APIs** (e.g. Opentrons) | Official API for one robot family. | Well documented, but ties the project to one vendor. |
| **Vendor method software** (e.g. Hamilton VENUS, Tecan FluentControl) | The proprietary editors most production methods are written in. | Where validated methods live today. Integration with external programs is vendor-specific. |
| **SiLA 2** | Lab automation standard: devices expose "Features" (commands, parameters, return values) over gRPC/HTTP/2. Version 1.0 released in 2019. | The natural integration point for real lab infrastructure. A SiLA 2 server for the liquid handler could sit behind the same validated tools. |

## Why this combination

- **Validation has to happen before the first movement.** Tool calls produce a complete plan as plain data, which can be replayed against the deck state and checked. Generated code or a step-by-step agent can't be checked the same way.
- **The model shouldn't be the safety mechanism.** The evaluation shows the same instruction handled differently across models and prompt versions. Deterministic checks outside the model don't move when the prompt does.
- **Hardware independence keeps the result transferable.** PyLabRobot makes it possible to run the whole study in simulation and keeps the design relevant to whichever robots a lab actually has.

## What would change the choice

- **More than one model or app using the same instruments:** move the tools behind an **MCP** server. The validator stays in front of the execution step, unchanged.
- **Integration with existing lab systems (LIMS, schedulers):** expose the instrument through **SiLA 2** and keep the LLM layer as one client among others.
- **Workflows too varied for a fixed tool set:** consider code generation, but only inside a sandbox, with the generated code reduced to the same validated actions before anything runs.

## Sources

- Boiko, D. A. et al. *Autonomous chemical research with large language models.* Nature (2023). Summary: [Carnegie Mellon University](https://www.cmu.edu/news/stories/archives/2023/december/cmu-designed-artificially-intelligent-coscientist-automates-scientific-discovery)
- Wierenga, R. P. et al. *PyLabRobot: An open-source, hardware-agnostic interface for liquid-handling robots and accessories.* (2023). [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10369895)
- [Standardization in Lab Automation (SiLA)](https://en.wikipedia.org/wiki/Standardization_in_Lab_Automation)
- [labmcp on PyPI](https://pypi.org/project/labmcp/)
