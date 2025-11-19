# QuizForge Discipline Module: Mathematics
**Calculations | Problem Solving | Formulas | Data Analysis**

---

## Overview

Math-specific guidance for numeric answers, formulas, word problems, multi-step solutions, and showing work.

**Load when:** Quiz involves calculations, geometry, algebra, statistics, or mathematical reasoning.

---

## Numerical Question Support (Production Ready)
- `Type: NUMERICAL` is now fully supported with tolerance and precision grading. Canonical specs live in `LLM_Modules/QF_BASE.md` and `LLM_Modules/QF_QTYPE_Numerical.md`.
- Use `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) when you need to expose all tolerance options to the LLM.
- Encourage precise prompts that state required units, rounding, or calculator access.
- Pick a single modifier per item (`Tolerance:`, `Precision:`, or `Range:`) to avoid conflicts.

---

## Numeric Questions (NUMERICAL type - EXPERIMENTAL ONLY)

### Basic Calculations

```
Type: NUMERICAL
Points: 8
Prompt:
Solve: 3x + 7 = 22

Answer: 5
```

---

### Decimals with Rounding

```
Type: NUMERICAL
Points: 10
Prompt:
Calculate the area of a circle with radius 5 cm. Use π ≈ 3.14159 and 
round to ONE decimal place.

Answer: 78.5
Range: 78.4 to 78.6
```

**Use ranges** when rounding introduces variance or multiple calculation methods exist.

---

### Word Problems

```
Type: NUMERICAL
Points: 12
Prompt:
A train travels 180 miles in 3 hours. What is its average speed in miles 
per hour?

Answer: 60
```

---

## Multi-Step Problems (MC or ESSAY)

**Use MC when answer is straightforward:**

```
Type: MC
Points: 12
Prompt:
A store sells shirts for $15 each. During a sale, they offer 20% off. 
How much would 3 shirts cost during the sale?

Choices:
- [ ] $45
- [ ] $40
- [x] $36
- [ ] $30
```

**Use ESSAY when you want students to show work:**

```
Type: ESSAY
Points: 15
Prompt:
Solve the following system of equations. Show all your work.

2x + 3y = 12
x - y = 1

Upload a photo of your work or type your step-by-step solution.
```

---

## Formulas and Equations

### Formula Application

```
Type: MC
Points: 10
Prompt:
Using the formula A = πr², find the area of a circle with radius 4 cm. 
(Use π ≈ 3.14)

Choices:
- [ ] 12.56 cm²
- [ ] 25.12 cm²
- [x] 50.24 cm²
- [ ] 100.48 cm²
```

---

### Identify the Correct Formula

```
Type: MC
Points: 8
Prompt:
Which formula correctly calculates the volume of a rectangular prism?

Choices:
- [ ] V = πr²h
- [x] V = lwh
- [ ] V = (1/2)bh
- [ ] V = 4πr³/3
```

---

## Geometry

### Shapes and Properties

```
Type: MC
Points: 8
Prompt:
How many sides does a hexagon have?

Choices:
- [ ] 5
- [x] 6
- [ ] 7
- [ ] 8
```

---

### Angle Relationships

```
Type: NUMERICAL
Points: 10
Prompt:
Two angles are supplementary. If one angle measures 65°, what is the 
measure of the other angle in degrees?

Answer: 115
```

---

## Data Analysis and Statistics

### Mean, Median, Mode

```
Type: NUMERICAL
Points: 12
Prompt:
Find the mean of the following data set: 12, 15, 18, 20, 25

Answer: 18
```

---

### Graph Interpretation

**Describe graph in stimulus, ask questions:**

```
Type: STIMULUS
Prompt:
The bar graph shows student test scores:

Score | Number of Students
------|-------------------
90-100|  8 students
80-89 | 12 students
70-79 |  6 students
60-69 |  4 students
---
Type: MC
Points: 8
Prompt:
How many students scored 80 or above?

Choices:
- [ ] 8
- [ ] 12
- [x] 20
- [ ] 30
---
Type: MC
Points: 10
Prompt:
What percentage of students scored below 70?

Choices:
- [ ] 10%
- [x] 33.3%
- [ ] 40%
- [ ] 50%
```

---

## Algebra

### Solving Equations

```
Type: FITB
Points: 10
Prompt:
Solve for x: 5x - 3 = 17

x = [answer]

Acceptable:
4
```

---

### Simplifying Expressions

```
Type: MC
Points: 10
Prompt:
Simplify: 3(x + 2) - 2x

Choices:
- [x] x + 6
- [ ] 5x + 6
- [ ] x + 2
- [ ] 3x + 4
```

---

## Fractions, Decimals, Percents

### Conversions

```
Type: NUMERICAL
Points: 8
Prompt:
Convert 3/4 to a decimal.

Answer: 0.75
```

---

### Operations

```
Type: MC
Points: 10
Prompt:
Calculate: 1/2 + 1/3

Choices:
- [ ] 2/5
- [ ] 1/6
- [x] 5/6
- [ ] 2/3
```

---

## Ratios and Proportions

```
Type: NUMERICAL
Points: 12
Prompt:
If 3 apples cost $2, how much would 12 apples cost?

Answer: 8
```

---

## Probability

```
Type: MC
Points: 10
Prompt:
A bag contains 5 red marbles and 3 blue marbles. What is the probability 
of drawing a red marble?

Choices:
- [ ] 3/8
- [x] 5/8
- [ ] 1/2
- [ ] 5/3
```

---

## Showing Work (File Upload or Essay)

**For complex problems requiring written solutions:**

```
Type: FILEUPLOAD
Points: 20
Prompt:
Solve the following problems. Show ALL your work for full credit.

1. Factor: x² + 7x + 12
2. Solve the inequality: 2x - 5 > 11
3. Find the slope of the line passing through (2,3) and (5,9)

**Format:** Upload a PDF or image of your handwritten work, or type your 
step-by-step solutions.

**Grading:**
- Correct answers: 12 points
- Clear work shown: 6 points
- Proper notation: 2 points
```

---

## Calculator Specification

**Note in prompt if calculator is allowed:**

```
Type: NUMERICAL
Points: 15
Prompt:
Calculate: √(144) + 5³

**Calculator allowed**

Answer: 137
```

---

## Units and Measurement

**Always specify units:**

```
Type: NUMERICAL
Points: 10
Prompt:
A rectangle has length 8 cm and width 5 cm. What is its perimeter in centimeters?

Answer: 26
```

---

## Common Mistakes to Avoid

### ❌ Don't Forget Units

**Bad:**
```
What is the area? (No units specified)
```

**Good:**
```
What is the area in square meters?
```

---

### ❌ Don't Make Rounding Ambiguous

**Bad:**
```
Round your answer.
```

**Good:**
```
Round to two decimal places.
```

---

### ❌ Don't Overlook Order of Operations

**Ensure distractors test PEMDAS understanding:**

```
Type: MC
Points: 8
Prompt:
Calculate: 2 + 3 × 4

Choices:
- [ ] 20
- [x] 14
- [ ] 24
- [ ] 18
```

**Strong distractor:** 20 (if student adds before multiplying)

---

## Assessment Balance for Math

**Recommended mix:**

- **30-40%** Calculation/computation
- **25-30%** Word problems (application)
- **15-20%** Formulas and concepts
- **10-15%** Data analysis and graphs
- **5-10%** Multi-step problem solving (with work shown)

**Example 20-question quiz (Pre-Algebra):**
- 8 Numerical (calculations)
- 6 MC (word problems, formulas)
- 3 MC (data interpretation)
- 2 FITB (solving for variables)
- 1 Essay or File Upload (multi-step problem with work)

---

## Summary

**Key principles for Math quizzes:**
✅ Always specify units  
✅ Clarify rounding expectations  
✅ Use ranges for decimal answers when appropriate  
✅ Mix calculation with application (word problems)  
✅ Include "show your work" questions for complex problems  
✅ Test conceptual understanding, not just computation  
✅ Specify calculator policy when relevant  

