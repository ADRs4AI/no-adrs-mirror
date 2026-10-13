You are writing a short public digest of ONE Architectural Deliberation Record (ADR) for a code mirror that deliberately omits the full record. Readers of the mirror get your digest instead of the document; they can request or cite the full record by its Address, which the tooling adds around your output — you do not need to write it.

Write in Markdown, at most 220 words, with exactly these sections:

**Decision** — two to four sentences: what was decided (or, if the record is still deliberating, what is being decided), its current status as the document states it, and why it mattered to the project. Plain language; a reader who has never seen the codebase should follow it.

**Open questions** — one bullet per question that the document marks as still open (`Status: unanswered`, `unresolved`, or `deferred`), in the form `QST-HANDLE — the question in one line (status)`. Copy handles exactly as written; they are citation anchors. Do NOT reproduce recommendations, answers, or the reasoning behind them — the digest points at the record, it does not replace it. If there are none, write "None open."

**What the full record holds** — one sentence naming what a reader would gain from the withheld document (e.g. the options weighed, the evidence cited, the iteration history).

Rules:
- Quote at most one sentence verbatim from the document; paraphrase otherwise.
- Never invent a status, a handle, a date, or a decision the document does not state. If the document is not an ADR (a seed, a template, a debrief), say so in one line under **Decision** and summarize what it is instead.
- Keep every name and model attribution exactly as the document gives it; do not add or remove credit.
- No preamble, no closing remarks, no headings other than the three above.
