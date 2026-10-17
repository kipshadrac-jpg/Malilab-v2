# Product Model

## Confirmed model

The initial product prioritizes this central learning loop:

**Playbook → Module → Lesson → Practice → Lab Tool → My Plan → Progress**

The initial product also includes the minimum necessary versions of **Notes**, user account and persistence, and **Badges or learning achievements**. Basic discovery and search are included where required by the approved UX. They support the core loop rather than expanding it into a complete implementation of every future capability.

1. A person discovers a relevant financial situation or question through a Playbook.
2. The Playbook connects the situation to relevant Modules.
3. The user studies Lessons in a Module.
4. Practice connects learning to the user's own circumstances and can use a Lab Tool to quantify and explore a scenario.
5. The user can capture learning in Notes and use My Plan to define and investigate a personal financial-freedom target, timeframe, assumptions, and possible path.
6. Progress reflects study and practical application; a minimal achievement record can evidence meaningful learning.
7. Related Playbooks and Modules support continued exploration.

This is an exploratory path, not a mandated linear course or a three-month completion deadline. The product should retain the relevant user account information and learning/planning progress so that the core loop can continue across use. Authentication details and persistence implementation are not product decisions here.

## Distinct concepts

- **Playbook:** A discovery and marketing entry point organized around a relatable financial situation, question, ambition, or problem. It investigates what needs to be understood and connects to learning and experiments; it does not simply give a financial answer.
- **Module:** A structured domain of financial knowledge containing an ordered set of Lessons and related learning resources. Example domains in the master specification are illustrative, not a final catalogue.
- **Lesson:** A primary learning unit in a Module, written and organized for accessible, practical study in Kenyan context.
- **Practice:** An exploratory activity that helps apply knowledge to a user's own situation. It may ask about goals, resources, available allocation, time, assumptions, and potentially relevant instruments.
- **Lab Tool:** A tool such as a calculator for exploring inputs, assumptions, scenarios, and outputs. Tools support practice; their catalogue and exact behaviors are not settled.
- **My Plan:** An initial core workspace where the user can define and investigate a personally meaningful financial-freedom target, timeframe, assumptions, and possible path based on their circumstances. It supports inquiry, not a promised outcome.
- **Notes:** Minimum necessary context-aware notes and insights connected to learning and, where useful, My Plan.
- **Progress:** A representation of study and practical application. Conceptually, a meaningful learning achievement combines Module completion with a practical plan attempt. Detailed states and thresholds remain undefined.
- **Badges or learning achievements:** The initial product should preserve and present a minimal record of meaningful learning achievement. Exact badge forms, award criteria, and mechanics remain undefined.
- **Dictionary:** A future full knowledge feature for accessible explanations of Kenyan financial terminology, linkable from Lessons and Playbooks as appropriate. A full Dictionary is not part of initial core scope.
- **Content production AI:** Internal assistance for research organization and content drafting, with human review before publication. Not the central user-facing product identity; it does not expand initial scope into an advanced user assistant.

## Discovery and progression

Discovery prioritizes Playbooks; Modules are discoverable as part of the broader library. Provide basic discovery and search where the approved UX requires it. Users may explore rather than follow a single fixed path. One illustrative progression is: discover a Playbook → select a Module → study Lessons → attempt Practice → explore a Lab Tool → complete a Module and attempt a plan → record learning Progress/achievement → discover related material. This does not establish mandatory gating or detailed award rules.

## Initial product scope

The initial product is the central learning loop above plus minimum necessary Notes, user account/persistence, and achievement support, with basic discovery/search as required by approved UX. Do not expand initial scope into full future capabilities. Subscription/payment, advanced monetization, advanced analytics, sophisticated recommendations, the full Dictionary, a large-scale financial knowledge graph, an advanced AI user assistant, and voice/audio remain future or out-of-scope capabilities unless later approved. The longer-term product vision retains these concepts where applicable.

## Product boundaries

- MaliLab is educational; it must not guarantee financial outcomes.
- A general user-facing AI chatbot is not required by this specification; an advanced AI user assistant is future scope.
- There is no speaker button, voice conversation, text-to-speech, podcast/audio lesson requirement, voice learning mode, or audio-first lesson format.
- Subscription/payment implementation is excluded from initial scope; the initial product phase is free.
- Advanced analytics, sophisticated recommendations, the full Dictionary, and a large-scale knowledge graph are future scope.
- Technology, data model, API, navigation architecture, final KPIs, and detailed interaction rules are not decided here.

## TODO/TO-BE-DEFINED

- Define detailed actions/thresholds for a Practice attempt, Module completion, progress, and achievement award mechanics. Conceptually, Module completion means completing the intended learning for a Module; a plan attempt means constructing and investigating a personal target, timeframe, assumptions, and possible path. Preserve evidence of completed learning and the user's plan attempt, including its target and assumptions and its relevant learning/Practice/Tool context where applicable.
- Define relationships/cardinality, prerequisites, optionality, and whether content is personalized.
- Define authentication, account lifecycle, and persistence implementation in a later phase.
- Define where basic discovery/search is required by the approved UX.
- Define the remaining detailed scope of Notes, achievements, and any future concepts.
