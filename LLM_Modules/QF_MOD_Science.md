# QuizForge Discipline Module: Science
**Lab-Based | Diagrams | Scientific Method | Data Analysis**

---

## Overview

Science-specific guidance for lab scenarios, experimental design, data interpretation, diagrams, and scientific reasoning.

**Load when:** Quiz involves biology, chemistry, physics, earth science, environmental science, or scientific inquiry.

---

## Numerical Question Support (Production Ready)
- `Type: NUMERICAL` now ships with Canvas-verified tolerance handling; see `LLM_Modules/QF_QTYPE_Numerical.md` for full mode descriptions.
- For quick authoring prompts, point the LLM at `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) rather than duplicating tolerance syntax here.
- Explicitly state units and measurement context in every prompt; have the LLM remind students when significant digits or decimal places matter.
- Choose one modifier per item (`Tolerance:`, `Precision:`, or `Range:`) to align with packager validation.

---

## Scientific Method Questions

### Hypothesis Identification

```
Type: MC
Points: 8
Prompt:
A student wants to test whether plants grow taller with more sunlight. 
Which is the BEST hypothesis?

Choices:
- [ ] Plants need sunlight
- [x] Plants exposed to more sunlight will grow taller than plants with less sunlight
- [ ] Sunlight makes plants happy
- [ ] I think sunlight helps plants
```

---

### Variables

```
Type: MC
Points: 10
Prompt:
In an experiment testing how temperature affects enzyme activity, what is 
the independent variable?

Choices:
- [x] Temperature
- [ ] Enzyme activity
- [ ] Time
- [ ] pH level
```

---

### Controls

```
Type: MC
Points: 10
Prompt:
Why is a control group important in an experiment?

Choices:
- [ ] To make the experiment faster
- [x] To provide a baseline for comparison
- [ ] To reduce the cost of the experiment
- [ ] To eliminate all variables
```

---

## Lab Scenarios (Use STIMULUS)

````
Type: STIMULUS
Prompt:
Read the following lab scenario and answer the questions.

>>>
**Experiment: Effect of Fertilizer on Plant Growth**

Setup:
- 20 identical bean plants, same age and size
- Group A (10 plants): Fertilizer added to soil
- Group B (10 plants): No fertilizer (control)
- All plants: Same amount of water, sunlight, temperature
- Measured height after 2 weeks

Results:
- Group A average height: 15 cm
- Group B average height: 10 cm
>>>
---
Type: MC
Points: 8
Prompt:
What is the dependent variable in this experiment?

Choices:
- [ ] Type of fertilizer
- [ ] Amount of water
- [x] Plant height
- [ ] Number of plants
---
Type: MC
Points: 10
Prompt:
Based on the results, what can you conclude?

Choices:
- [ ] Fertilizer is bad for plants
- [x] Fertilizer appears to increase plant growth
- [ ] All plants need fertilizer
- [ ] The experiment failed
---
Type: ESSAY
Points: 15
Prompt:
Identify ONE way to improve this experiment and explain why your suggestion 
would make the results more reliable. (5-8 sentences)
````

---

## Data Analysis

### Graph Interpretation

```
Type: STIMULUS
Prompt:
The line graph shows temperature change over 24 hours:

Time | Temperature (°C)
-----|---------------
6 AM | 15
12 PM| 25
6 PM | 20
12 AM| 10
---
Type: MC
Points: 8
Prompt:
At what time was the temperature highest?

Choices:
- [ ] 6 AM
- [x] 12 PM
- [ ] 6 PM
- [ ] 12 AM
---
Type: NUMERICAL
Points: 10
Prompt:
What was the temperature change between 6 AM and 12 PM in degrees Celsius?

Answer: 10
```

---

### Calculations from Data

```
Type: NUMERICAL
Points: 12
Prompt:
A car travels 300 kilometers in 5 hours. Calculate its average speed in 
kilometers per hour.

Answer: 60
```

---

## Biological Concepts

### Cell Structure

```
Type: MATCHING
Points: 12
Prompt:
Match each cell organelle to its function.

Pairs:
Mitochondria = Produces energy (ATP)
Nucleus = Contains genetic material (DNA)
Chloroplast = Site of photosynthesis
Cell membrane = Controls what enters/exits the cell
```

---

### Life Processes

```
Type: MC
Points: 10
Prompt:
Which process do plants use to make food from sunlight?

Choices:
- [ ] Cellular respiration
- [x] Photosynthesis
- [ ] Transpiration
- [ ] Germination
```

---

## Chemistry Concepts

### Atoms and Elements

```
Type: MC
Points: 8
Prompt:
What is the chemical symbol for water?

Choices:
- [ ] W
- [ ] Wa
- [x] H₂O
- [ ] O₂H
```

**Note:** Use subscripts with regular numbers: H₂O (not H2O in choices)

---

### Chemical Reactions

```
Type: MC
Points: 10
Prompt:
In a chemical reaction, what are the starting materials called?

Choices:
- [ ] Products
- [x] Reactants
- [ ] Catalysts
- [ ] Solutions
```

---

## Physics Concepts

### Forces and Motion

```
Type: NUMERICAL
Points: 12
Prompt:
An object with mass 5 kg is pushed with a force of 20 N. Using F = ma, 
calculate its acceleration in m/s².

Answer: 4
```

---

### Energy

```
Type: MC
Points: 10
Prompt:
A ball at the top of a hill has what type of energy?

Choices:
- [ ] Kinetic
- [x] Potential
- [ ] Thermal
- [ ] Chemical
```

---

## Earth Science

### Rock Cycle

```
Type: MC
Points: 8
Prompt:
Which type of rock forms from cooled lava or magma?

Choices:
- [x] Igneous
- [ ] Sedimentary
- [ ] Metamorphic
- [ ] Fossilized
```

---

### Weather and Climate

```
Type: MC
Points: 10
Prompt:
What causes the seasons on Earth?

Choices:
- [ ] Distance from the Sun
- [x] Tilt of Earth's axis
- [ ] Speed of Earth's rotation
- [ ] Amount of pollution
```

---

## Diagrams and Models

**Describe diagrams in text:**

```
Type: STIMULUS
Prompt:
Study the diagram of the water cycle:

>>>
The diagram shows:
1. Evaporation: Water from oceans/lakes rises as vapor
2. Condensation: Vapor cools and forms clouds
3. Precipitation: Rain/snow falls to Earth
4. Collection: Water returns to bodies of water
>>>
---
Type: MC
Points: 8
Prompt:
During which stage does water vapor turn into liquid water?

Choices:
- [ ] Evaporation
- [x] Condensation
- [ ] Precipitation
- [ ] Collection
```

---

## Classification

```
Type: MATCHING
Points: 15
Prompt:
Match each organism to its classification.

Pairs:
Oak tree = Plant
Eagle = Bird
Frog = Amphibian
Shark = Fish
Mushroom = Fungus
```

---

## Safety and Ethics

```
Type: MC
Points: 8
Prompt:
What should you do FIRST if a chemical spills in the lab?

Choices:
- [ ] Call 911
- [ ] Clean it up yourself
- [x] Alert the teacher immediately
- [ ] Ignore it if it's small
```

---

## Environmental Science

```
Type: ESSAY
Points: 20
Prompt:
Explain how human activities contribute to climate change. Include at 
least THREE specific examples and describe their environmental impacts. 
(4-5 paragraphs)
```

---

## Vocabulary in Context

```
Type: FITB
Points: 6
Prompt:
The process by which organisms with advantageous traits survive and 
reproduce is called natural [answer].

Acceptable:
selection
```

---

## Assessment Balance for Science

**Recommended mix:**

- **25-35%** Content knowledge (facts, vocabulary, concepts)
- **25-35%** Scientific method and inquiry
- **20-25%** Data analysis and interpretation
- **10-15%** Application and problem-solving
- **5-10%** Lab safety and procedures

**Example 20-question quiz (Biology - Cells):**
- 7 MC on cell structure/function
- 5 MC on scientific method/experimental design
- 3 MC on data interpretation
- 2 Matching (organelles to functions)
- 2 Numerical (calculations from data)
- 1 Essay (lab scenario analysis)

---

## Summary

**Key principles for Science quizzes:**
✅ Use lab scenarios as stimuli  
✅ Test scientific thinking, not just memorization  
✅ Include data analysis questions  
✅ Connect concepts to real-world applications  
✅ Emphasize safety when relevant  
✅ Use diagrams/models described in text  
✅ Mix content knowledge with inquiry skills  

