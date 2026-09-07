# Prerequisite tree

Parse only the target course's direct requirements_text. Do not expand a prerequisite
into its own prerequisites. Preserve alternatives, conjunctions, exclusions,
concurrency, minimum grades, placement, standing, credits, programs, and consent.
Recommended preparation in a description is not an eligibility requirement.

Return a best-effort flat tree. Each node has a unique short ID; children are IDs.
The root reaches every node exactly once, without cycles. all/any need at least two
children; not needs one; leaves have none. Every node includes course and condition,
using null when inapplicable. A single requirement is its own root.

Course leaves use linked canonical references, timing prior unless concurrency is
explicit, and minimum_grade null unless stated. Keep a course's grade inside its
course node. Preserve other rules as verbatim condition leaves. Each node's evidence
is an exact source substring; operators may quote the entire relevant clause. If a
clause cannot be split without inventing words, keep it as one condition.

Inherit subjects across numbered lists using source_reference_spans when available;
retain literal shorthand in quotes. Missing spaces around links do not remove an
explicit and/or. An and within a program name does not split that program. Unresolved
course references remain condition leaves, with needs_review and an explanatory note.

Keep global credit exclusions separate from positive eligibility:
“A or B. Not open to students with credit for C or D” means
all(any(A,B),not(any(C,D))). Quote the complete exclusion sentence for the not node.

For ambiguous grouping, return your best tree with needs_review and state the
assumption. Bare semicolons between preparation, graduate standing, or certificate
membership may indicate alternatives; prefer OR unless context indicates otherwise,
and mark that inference for review. Do not omit a tree just because punctuation is
ambiguous. If no decomposition is possible, use one original-text condition node.
Explicitly empty or None requirements use status none, root null, and nodes [].
The display exporter supplies a placeholder for empty trees.

Use at most four brief factual notes for needs_review, not deliberation. Use notes []
for parsed or none. The tree is a display interpretation, not an eligibility decision.
