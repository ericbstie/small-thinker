---
status: accepted
---

# Decompose sentences into propositional content only

The original plan broke every training sentence into four pragmatic facets —
propositional content, presupposition, illocutionary force, and pragmatic
implicature — each vectorised as its own chunk. We are keeping **only the
propositional-content facet** and dropping the other three, because our corpus
is expository Wikipedia prose where the other three are near-constant or empty,
and because the extraction method we are replicating (AFEV atomic-fact
extraction) only produces propositional content in the first place.

## Considered options

- **Four facets (propositional content, presupposition, illocutionary force,
  pragmatic implicature).** The initial design. Rejected: on third-person
  declarative encyclopedic text, illocutionary force collapses to a near-constant
  "assertive", and most factual sentences carry no conversational implicature and
  little presupposition beyond their literal proposition. Three of the four buckets
  would be sparse or low-signal, so downstream vector clustering would be dominated
  by propositional-content chunks regardless. The three extra facets also each need
  their own subsystem (trigger lexicons, dialogue-act classifiers, Gricean CoT) —
  none of which fall out of the AFEV method — for little added signal.
- **Propositional content only (chosen).** A single facet, produced directly by
  the AFEV-style iterative atomic-fact extractor. One method, one bucket, no
  bolted-on pragmatics subsystems.

## Consequences

- The sentence-dissecting step is a single AFEV-style extractor emitting
  decontextualised atomic propositions; there is no presupposition,
  illocutionary-force, or implicature output.
- Each atomic proposition is still vectorised individually, so the "atomic parts
  land in buckets" clustering step downstream is unchanged in shape — only the
  facet count shrinks from four to one.
- Reintroducing the pragmatic facets later is a real cost (new subsystems), so
  this is recorded as a deliberate boundary rather than an oversight. If a future
  corpus includes dialogue or first-person text where illocutionary force and
  implicature vary, this decision should be revisited.
