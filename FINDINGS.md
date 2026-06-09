# VoiceIQ — Methodology & Findings

## What VoiceIQ Measures and Why

VoiceIQ evaluates AI voice agents across five dimensions, each chosen because it catches a distinct class of production failure:

| Dimension | What It Catches |
|---|---|
| **Response Relevance** | Agent gives technically correct but off-topic answers, ignores the caller's actual question, or regurgitates scripted responses that don't address the situation. Common failure: caller asks about cancellation policy, agent pitches an upgrade. |
| **Objection Handling** | Agent collapses when the caller pushes back — either folding immediately ("okay, I'll cancel that") or looping on the same rebuttal verbatim. This is where most agents break under pressure. |
| **Conversation Flow** | Awkward transitions, abrupt topic changes, talking over the caller's concern, or getting stuck in dead-end loops. Flow failures make callers hang up even when the agent's content is correct. |
| **Empathy** | Agent fails to acknowledge frustration, dismisses emotional context, or delivers bad news with zero softening. Produces the "talking to a wall" experience that tanks caller satisfaction. |
| **Goal Completion** | The bottom line: did the agent accomplish what the call was supposed to achieve? An agent can score well on every other dimension and still fail if it never actually resolves the issue, books the appointment, or closes the sale. |

Testing uses realistic simulated callers — not generic "say something angry" prompts. Each simulated caller has a distinct persona (patience level, communication style, objection patterns) and specific hang-up triggers that terminate the conversation if the agent mishandles them. This forces the agent to handle the kind of variance real callers produce.

## How the Judge Works

The judge is an LLM (llama3:8b running locally via Ollama) that reads complete conversation transcripts and produces structured evaluations.

**Scoring:** The judge outputs a 0–100 score for each of the five dimensions. Every score must include mandatory turn-level evidence citations — the specific turns in the transcript that justify the score. A score without a citation is invalid. This eliminates vibes-based evaluation where the judge "feels like" the conversation went well but can't point to why.

**Failure Identification:** Beyond scores, the judge identifies specific failure points: the exact turn where something went wrong and a concrete reason (e.g., "Turn 7: Agent ignored caller's price objection and repeated the same feature list from Turn 4"). This is often more useful than the scores themselves — it tells you exactly what to fix.

**Recommendations:** Each evaluation includes 2–4 actionable recommendations. These are specific enough to act on ("Add a price-anchoring response before presenting the premium tier") rather than generic ("Improve objection handling").

## Judge Weighting Rationale

The overall score is a weighted composite:

```
overall = 0.25 × goal_completion
        + 0.20 × response_relevance
        + 0.20 × objection_handling
        + 0.20 × conversation_flow
        + 0.15 × empathy
```

**Goal completion gets the highest weight (0.25)** because it's the bottom line. A voice agent exists to accomplish something — schedule an appointment, resolve a complaint, close a sale. An agent that's empathetic, relevant, and smooth but fails to actually do its job is a polite failure. In production, goal completion is what drives business metrics.

**Response relevance, objection handling, and conversation flow share equal weight (0.20 each).** These are the three execution dimensions — they measure *how* the agent gets to goal completion. Deficiencies in any of these directly cause goal failure or caller abandonment, so they're weighted equally.

**Empathy gets the lowest weight (0.15)** — not because it doesn't matter, but because it's the hardest dimension for an LLM judge to assess reliably. Empathy is nuanced, culturally dependent, and often conveyed through tone and pacing that a transcript flattens. The judge can catch obvious empathy failures (ignoring explicit frustration, delivering bad news bluntly) but will miss subtle ones. Weighting it lower prevents noisy empathy scores from distorting the overall assessment.

## Calibration Methodology

The judge is only useful if you can prove it's trustworthy. VoiceIQ includes a calibration harness that quantifies exactly how much you should trust the judge's output.

### The Human Calibration Loop

1. A human evaluator reads the same conversation transcripts the judge sees.
2. The human independently provides per-dimension scores (0–100) and identifies failure points.
3. Neither the human nor the judge sees the other's output during evaluation.
4. Statistical agreement metrics are computed between the two.

### Agreement Metrics

| Metric | What It Tells You |
|---|---|
| **MAE (Mean Absolute Error)** | Average magnitude of disagreement in score points. MAE < 10 means the judge is "close enough" for screening. MAE > 15 means the judge needs prompt tuning. |
| **Pearson r** | Linear correlation — does the judge's ranking of conversations match the human's? High r (> 0.8) means the judge reliably distinguishes good from bad. |
| **Spearman ρ** | Rank correlation — same idea as Pearson but robust to nonlinear relationships. Important because the relationship between judge and human scores may not be perfectly linear. |
| **Bland-Altman bias** | Systematic offset — is the judge consistently scoring higher or lower than the human? A bias of +8 means the judge is lenient by ~8 points on average. |
| **Bland-Altman limits of agreement** | The range within which 95% of judge-human disagreements fall. Tells you the worst-case disagreement you should expect. |
| **Failure point precision** | Of the failure points the judge flagged, what fraction did the human agree with? Low precision = the judge hallucinates problems. |
| **Failure point recall** | Of the failure points the human identified, what fraction did the judge catch? Low recall = the judge misses real problems. |
| **Failure point Jaccard** | Overlap between judge and human failure point sets. A single number that captures both precision and recall. Jaccard > 0.5 is a reasonable bar for a screening tool. |

> **Note on seed data:** The initial seeded dataset uses illustrative placeholder scores to demonstrate the calibration pipeline and dashboard. These scores are not from a real calibration run. Replace them with actual human evaluations before drawing any conclusions about judge trustworthiness.

## Judge Reliability & Limitations

Honest accounting of where the judge can and cannot be trusted.

### Self-Consistency

The judge evaluates each transcript 3 times. If the standard deviation across runs exceeds 10 points on any dimension, that score is flagged as low confidence. High variance means the judge is uncertain — the prompt doesn't sufficiently constrain the evaluation for that scenario type, or the transcript is genuinely ambiguous.

### Known Weaknesses

- **Leniency bias.** LLM judges — including this one — tend to score higher than humans. Expect a positive Bland-Altman bias until you've tuned the prompts to compensate.
- **Subtle tone blindness.** The judge processes text transcripts. It cannot hear vocal tone, pacing, or silence. A response that reads fine on paper may have been delivered in a way that feels dismissive or rushed. The judge will miss this.
- **Empathy is least reliable.** Empathy assessment requires understanding emotional context, cultural norms, and implicit communication. The judge catches explicit empathy failures but will miss nuance. This is why empathy is weighted lowest.
- **Model size matters.** These findings assume llama3:8b. Smaller models (e.g., 3b parameter variants) will produce less consistent scores, worse failure point identification, and more frequent hallucinated evidence citations. If you downsize the model, re-run calibration — don't assume prior calibration results transfer.

### What the Judge Is and Isn't

The judge is a **screening tool**. It surfaces conversations and failure patterns worth human attention. It is not a replacement for human evaluation. Use it to:

- Catch regressions before they ship
- Identify which scenario types your agent handles worst
- Prioritize which conversations a human should review

Do not use it to make final quality decisions without human verification, especially for edge cases or high-stakes deployments.

## Key Findings

<!-- TODO: [YOUR NAME] — Replace with real findings after running calibration -->
**Finding 1:** [After running all 6 scenarios 3x each, which scenario type do agents fail most consistently on?]

**Finding 2:** [At what average turn number does objection handling typically collapse?]

**Finding 3:** [What is the actual MAE between your hand-scores and the judge? Is it < 10 (good) or > 15 (concerning)?]

**Finding 4:** [Which dimension shows the highest judge self-consistency variance? Why?]

**Finding 5:** [What single prompt modification produced the largest score improvement across scenarios?]
