# Inclusive and model-neutral analysis

Use this checklist when language, locale, accessibility, personal data, or consequential decisions may affect interpretation.

## Preserve before normalizing

- Preserve original cell text, image bytes, Unicode, formula text, units, and coordinates.
- Record detected or user-supplied language, script, writing direction, locale, calendar, decimal separator, and date convention when material.
- Store translations, transliterations, unit conversions, and normalized dates as derived values. Never overwrite the source representation.
- Do not assume left-to-right reading order. Check right-to-left, vertical, bidirectional, and mixed-script layouts.
- Keep blank, zero, unavailable, not applicable, redacted, and unknown as distinct states.

## Avoid unsupported inferences

- Do not infer identity, gender, ethnicity, nationality, disability, socioeconomic status, competence, sentiment, or intent from names, language, images, formatting, or assistive annotations.
- Describe observable document evidence instead of labeling a person or group.
- When analysis affects eligibility, safety, employment, health, finance, education, or legal rights, require the appropriate qualified review and disclose automation limits.

## Make evidence accessible

- Preserve alt text, captions, object names, and reading order, but flag conflicts with visible or structural evidence.
- Provide text alternatives for image-derived findings and do not rely on color, position, or shape alone to communicate status.
- Use explicit labels in addition to symbols such as color, stars, circles, and warning icons.
- Ask for or recommend an accessible source when low resolution, handwriting, color contrast, or complex spatial layout prevents reliable extraction.

## Stay backend-neutral

- Select OCR, rules, local models, hosted models, or qualified manual transcription based on evidence needs, authorization, language coverage, accessibility, cost, and reproducibility.
- Record backend class, product or project name when known, version, configuration, timestamp, and input hash. Do not imply that one vendor is authoritative.
- Compare outputs against source evidence. Agreement between multiple systems increases corroboration only when their errors are sufficiently independent.
- If no suitable backend is available, report `NOT_ANALYZED` and the reason instead of fabricating or silently omitting content.

## Report uncertainty without false precision

- Prefer calibrated labels with reasons: `HIGH`, `MEDIUM`, `LOW`, `CONFLICT`, `NOT_ANALYZED`, or `UNKNOWN`.
- Use numeric confidence only when the producing system defines and validates the scale for the relevant language and document type.
- Separate extraction certainty from interpretation certainty.
- State which populations, languages, layouts, or workbook features were not tested.

## Minimize exposure

- Include only the cells and media needed for the task.
- Check whether absolute paths, usernames, document properties, comments, hidden content, external links, and image metadata disclose sensitive information before sharing artifacts.
- Apply the user's organizational policy, retention rules, consent requirements, and applicable jurisdiction. When these are unknown, keep processing local and disclose the limitation.
