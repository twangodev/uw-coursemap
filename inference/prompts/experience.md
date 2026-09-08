# Student experience

Use only the target course's supplied reviews, never grades, catalog claims, or
instructor reputation. No reviews means insufficient_evidence with themes [].
Produce at most six useful themes, balancing supported praise and criticism.

Cite the supplied citation_id handles (such as review:1) in review_ids. Copy them
exactly; do not reconstruct hashes. Cite only comments supporting that theme.
Runtime resolves IDs and attaches original comments, instructors, dates, and counts.

Make instructor feedback actionable: name the professor using the exact supplied
instructor_name, set subject_instructor_id, and cite only that professor's reviews
for this course. Split feedback about different professors into separate themes.
Teaching-clarity themes and single-instructor overall themes must name their subject.
General course themes use subject_instructor_id null. A mention of another professor
inside a comment does not make it a review of that professor.

Use wording such as “Cited reviews praise Jane Doe for clear explanations” or
“One reviewer recommends Jane Doe.” Describe a preference only if a cited comment
explicitly expresses it. Do not infer rankings, majority preference, or prevalence
from this sample. Avoid “widely,” “generally,” and “frequently” as population claims.

Earlier instructors and older reviews are valid historical evidence. Do not present
them as facts about the current offering. Runtime supplies the cited year range;
omit a separate date range from the summary.
