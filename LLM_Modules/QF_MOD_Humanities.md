# QuizForge Discipline Module: Humanities
**History | Government | Economics | Geography | Sociology | Psychology**

---

## Overview

Humanities-specific guidance for historical analysis, primary source interpretation, civic knowledge, and social science concepts. Covers middle school through high school (grades 6-12).

**Load when:** Quiz involves history, government, economics, geography, sociology, psychology, or integrated social studies content.

---

## Rigor Calibration

**Foundations (Grades 6-8):**
- Focus on factual recall, basic chronology, and simple cause/effect
- Who, what, when, where questions dominate
- Simple primary source interpretation (identify main idea, literal meaning)
- Examples: "When did the Civil War begin?" | "What was the main cause of WWI?"

**Intermediate (Grades 9-10):**
- Add comparative analysis, multiple causation, and historical significance
- Why and how questions increase
- Primary source analysis includes context and bias
- Examples: "How did Enlightenment ideas influence the American Revolution?" | "Compare economic systems"

**Advanced (Grades 11-12, AP):**
- Historiography, synthesis across sources, complex argumentation
- Evaluate interpretations, assess continuity/change over time
- Multiple document analysis with synthesis (DBQ-style)
- Examples: "Evaluate the extent to which..." | "To what degree did..." | Synthesis of 6-8 sources

**Adjust question complexity to match student level; avoid mixing rigor tiers within a single quiz.**

---

## Quantitative Integrations
- Use `Type: NUMERICAL` sparingly for data-table analysis or economics problems; point the LLM to `LLM_Modules/QF_BASE.md` for field syntax.
- When tolerances or ranges are necessary, reference `LLM_Modules/QF_QTYPE_Numerical.md` or `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) instead of restating logic in this module.

---

## Primary Source Analysis

### Use STIMULUS for historical documents

````
Type: STIMULUS
Prompt:
Read the following excerpt from the Declaration of Independence (1776) 
and answer the questions that follow.

>>>
[1] We hold these truths to be self-evident, that all men are created equal, 
that they are endowed by their Creator with certain unalienable Rights, that 
among these are Life, Liberty and the pursuit of Happiness.

[2] That to secure these rights, Governments are instituted among Men, deriving 
their just powers from the consent of the governed, That whenever any Form of 
Government becomes destructive of these ends, it is the Right of the People to 
alter or to abolish it.
>>>
---
Type: MC
Points: 8
Prompt:
According to paragraph 1, where do rights come from?

Choices:
- [ ] The government
- [x] They are natural/God-given
- [ ] The king
- [ ] The Constitution
---
Type: ESSAY
Points: 15
Prompt:
In 5-8 sentences, explain what the phrase "consent of the governed" means 
and why it was revolutionary for its time. Use evidence from the passage.
````

**Best practices:**
- Provide context (author, date, situation)
- Use paragraph numbering for citations
- Ask for textual evidence in essays
- Connect to broader historical themes

---

## Common Question Patterns

### Historical Cause and Effect

```
Type: MC
Points: 10
Prompt:
Which factor was the PRIMARY cause of World War I?

Choices:
- [ ] The assassination of Archduke Franz Ferdinand
- [x] The complex system of European alliances
- [ ] Economic depression in Germany
- [ ] The Treaty of Versailles
```

**Strong distractor:** The assassination (trigger vs. underlying cause)

---

### Chronology / Sequencing

```
Type: MC
Points: 8
Prompt:
Which event happened FIRST?

Choices:
- [ ] The Civil War
- [x] The American Revolution
- [ ] World War I
- [ ] The Spanish-American War
```

---

### Geographic Analysis

```
Type: MC
Points: 10
Prompt:
The Mississippi River was important to early American settlements because:

Choices:
- [ ] It provided drinking water
- [x] It enabled trade and transportation
- [ ] It marked the border with Canada
- [ ] It was used for irrigation only
```

---

### Civic/Government Concepts

```
Type: MC
Points: 8
Prompt:
In the U.S. system of checks and balances, which branch can veto legislation?

Choices:
- [ ] Legislative
- [x] Executive
- [ ] Judicial
- [ ] None of the above
```

---

### Economic Principles

```
Type: MC
Points: 10
Prompt:
According to the law of supply and demand, what happens to price when 
demand increases and supply stays the same?

Choices:
- [ ] Price decreases
- [x] Price increases
- [ ] Price stays the same
- [ ] Price becomes unpredictable
```

---

## Map-Based Questions

**Describe maps in text, reference in questions:**

```
Type: STIMULUS
Prompt:
Study the following description of the map showing European colonial 
territories in Africa, 1914:

>>>
The map shows Africa divided into colonial territories. The key indicates:
- British territories (red): Egypt, South Africa, Kenya, Nigeria
- French territories (blue): Algeria, West Africa, Madagascar
- German territories (green): Tanganyika, Cameroon, Southwest Africa
- Belgian territories (yellow): Congo
- Independent nations: Liberia, Ethiopia
>>>
---
Type: MC
Points: 8
Prompt:
Which European power controlled the most territory in Africa by 1914?

Choices:
- [x] Britain
- [ ] France
- [ ] Germany
- [ ] Belgium
```

**Note:** For actual visual maps, use Canvas's native image upload feature after QTI import.

---

## Timeline Questions

```
Type: MATCHING
Points: 12
Prompt:
Match each event to its decade.

Pairs:
American Revolution = 1770s
Civil War = 1860s
World War I = 1910s
Great Depression = 1930s
```

---

## Perspective / Point of View

```
Type: MC
Points: 10
Prompt:
A Northern newspaper in 1850 would most likely describe slavery as:

Choices:
- [ ] A necessary economic system
- [x] A moral evil that should be abolished
- [ ] A states' rights issue
- [ ] An accepted practice worldwide
```

---

## Historical Interpretation

```
Type: ESSAY
Points: 20
Prompt:
Historians debate whether the New Deal successfully ended the Great Depression 
or if World War II was the primary factor. In 4-5 paragraphs, present both 
viewpoints and explain which argument you find more convincing based on 
historical evidence.

**Include:**
- Summary of New Deal programs
- Economic data (if known)
- Impact of WWII on employment/production
- Your reasoned conclusion
```

---

## Vocabulary in Context

**Humanities-specific terms:**

```
Type: FITB
Points: 6
Prompt:
A system of government where power is divided between national and state 
governments is called [answer].

Acceptable:
federalism, federal system
```

---

```
Type: MC
Points: 8
Prompt:
In economics, "inflation" refers to:

Choices:
- [ ] Decrease in prices over time
- [x] Increase in prices over time
- [ ] Government regulation of prices
- [ ] International trade agreements
```

---

## Compare and Contrast

```
Type: ESSAY
Points: 15
Prompt:
Compare and contrast the governments of ancient Athens and ancient Sparta. 
Include at least TWO similarities and TWO differences. (5-8 sentences)
```

---

## Document-Based Questions (DBQ Style)

**Multiple sources, synthesis required:**

````
Type: STIMULUS
Prompt:
Read Source A: Excerpt from Frederick Douglass's autobiography (1845)
>>>
[Source A text]
>>>
---
Type: STIMULUS
Prompt:
Read Source B: Letter from a Southern plantation owner (1850)
>>>
[Source B text]
>>>
---
Type: ESSAY
Points: 25
Prompt:
Using evidence from BOTH sources, analyze the different perspectives on 
slavery in the antebellum South. How do these sources reflect the regional 
divisions that led to the Civil War? (4-5 paragraphs)
````

---

## Cultural and Social Concepts

### Psychology

```
Type: MC
Points: 8
Prompt:
According to Maslow's hierarchy of needs, which need must be satisfied FIRST?

Choices:
- [ ] Self-esteem
- [ ] Belonging
- [x] Physiological needs (food, water, shelter)
- [ ] Self-actualization
```

---

### Sociology

```
Type: MC
Points: 10
Prompt:
The process by which individuals learn the norms and values of their 
society is called:

Choices:
- [ ] Acculturation
- [x] Socialization
- [ ] Assimilation
- [ ] Integration
```

---

## Current Events Connection

```
Type: ESSAY
Points: 20
Prompt:
How does the concept of "checks and balances" from the U.S. Constitution 
apply to a recent news event? Describe a specific example from the past year 
and explain which branches of government were involved. (5-8 sentences)
```

---

## Assessment Balance for Humanities

**Recommended mix:**

- **30-40%** Factual knowledge (dates, people, events, definitions)
- **25-35%** Analysis and interpretation (cause/effect, compare/contrast)
- **15-20%** Primary source analysis
- **10-15%** Application to current events or broader themes
- **10-15%** Writing (document analysis, argumentation)

**Example 20-question quiz on American Revolution:**
- 6 MC on key events/people
- 5 MC on causes and effects
- 4 MC on primary source interpretation
- 2 MC on geographic/economic factors
- 2 Essay (1 short response on documents, 1 extended on larger themes)
- 1 Matching (events to dates/significance)

---

## Summary

**Key principles for Humanities quizzes:**
✅ Use primary sources with proper context  
✅ Focus on analysis, not just memorization  
✅ Connect past to present when relevant  
✅ Ask for evidence-based reasoning  
✅ Include multiple perspectives  
✅ Balance factual recall with critical thinking  
✅ Use maps, timelines, and documents as stimuli  

