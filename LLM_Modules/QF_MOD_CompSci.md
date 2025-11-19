# QuizForge Discipline Module: Computer Science
**Code-Heavy Assessments | Syntax Highlighting | Debugging Questions**

---

## Overview

This module provides CS-specific guidance for creating programming assessments with proper code formatting, syntax highlighting, and common CS question patterns.

**Load when:** Quiz involves programming concepts, code analysis, debugging, algorithms, or any CS content.

---

## Numerical Items
- Use `Type: NUMERICAL` for algorithm runtime estimates or data-set calculations when a single numeric value is required.
- Keep prompts explicit about units (e.g., milliseconds, operations) and cite `LLM_Modules/core/QF_BASE.md` for field syntax.
- If tolerance or precision constraints are needed, reference `LLM_Modules/QF_QTYPE_Numerical.md` or `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) instead of restating rules here.

---

## Code Formatting

### Fenced Code Blocks (Automatic Monokai Theme)

**Use triple backticks with language specification:**

````
```python
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)
```
````

**Supported languages:** `python`, `java`, `javascript`, `cpp`, `c`, `html`, `css`, `sql`, `bash`

**Automatic styling:**
- Dark background (#272822)
- Syntax highlighting (keywords, strings, comments, functions)
- Preserved indentation and spacing
- Monospace font

---

## Common CS Question Patterns

### 1. Code Output Prediction

**Pattern:** Show code, ask what it outputs

```
Type: MC
Points: 8
Prompt:
What will this code output?

```python
x = 5
y = 10
print(x + y)
```

Choices:
- [ ] 510
- [x] 15
- [ ] xy
- [ ] Error
```

**Best practice:** Use clear, simple code snippets. Avoid overly complex examples that test puzzle-solving more than concept understanding.

---

### 2. Bug Identification

**Pattern:** Show buggy code, identify the error

```
Type: MC
Points: 10
Prompt:
The following code is supposed to calculate the average of three numbers, 
but it has a bug. What is the error?

```python
def average(a, b, c):
    total = a + b + c
    return total / 2
```

Choices:
- [ ] Missing return statement
- [ ] Variable 'total' not defined
- [x] Should divide by 3, not 2
- [ ] Parameters should be *args
```

---

### 3. Syntax Correction

**Pattern:** Identify correct syntax

```
Type: MC
Points: 6
Prompt:
Which of the following correctly defines a list in Python?

Choices:
- [x] `my_list = [1, 2, 3]`
- [ ] `my_list = (1, 2, 3)`
- [ ] `my_list = {1, 2, 3}`
- [ ] `my_list = <1, 2, 3>`
```

**Note:** Use inline code (backticks) for short syntax examples in choices.

---

### 4. Concept Application

**Pattern:** Apply programming concept to scenario

```
Type: MC
Points: 10
Prompt:
You need to store student names and their corresponding grades. Which 
data structure is most appropriate?

Choices:
- [ ] List
- [ ] Tuple
- [x] Dictionary
- [ ] Set
```

---

### 5. Code Completion (FITB)

**Pattern:** Fill in missing code

```
Type: FITB
Points: 8
Prompt:
Complete the code to print "Hello, World!" in Python.

```python
[answer]("Hello, World!")
```

Acceptable:
print
```

---

### 6. Algorithm Analysis

**Pattern:** Analyze algorithm efficiency or behavior

```
Type: ESSAY
Points: 15
Prompt:
The following code uses a bubble sort algorithm:

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
```

In 5-8 sentences, explain:
1. How this algorithm works
2. What its time complexity is
3. When you might choose a different sorting algorithm
```

---

## CS-Specific Best Practices

### Comments in Code Examples

**Include comments for clarity when code is complex:**

````
```python
def fibonacci(n):
    # Base cases
    if n <= 1:
        return n
    # Recursive case
    return fibonacci(n-1) + fibonacci(n-2)
```
````

**Don't over-comment trivial code:**
````
```python
# Good: Clear without excessive comments
x = 5
y = 10
print(x + y)

# Bad: Over-commented
x = 5  # assign 5 to x
y = 10  # assign 10 to y
print(x + y)  # print the sum of x and y
```
````

---

### Indentation Matters

**Python, YAML, and other indent-sensitive languages:**
- Preserve exact indentation in code blocks
- Use spaces (4 spaces standard for Python)
- Avoid mixing tabs and spaces

````
```python
def greet(name):
    if name:
        print(f"Hello, {name}!")
    else:
        print("Hello, stranger!")
```
````

---

### Error Messages

**When showing error output, format clearly:**

````
```
Traceback (most recent call last):
  File "example.py", line 3, in <module>
    print(undefined_variable)
NameError: name 'undefined_variable' is not defined
```
````

---

## Language-Specific Considerations

### Python
- Use `def` for functions, `:` for blocks
- Indentation defines scope
- Case-sensitive (`Print` ≠ `print`)
- Use `#` for comments

### Java
- Use `public static void main(String[] args)` for entry point
- Semicolons required `;`
- Curly braces `{}` for blocks
- Use `//` for single-line comments, `/* */` for multi-line

### JavaScript
- Semicolons optional but recommended
- Use `let`/`const` for variables (not `var`)
- Arrow functions: `() => {}`
- Use `//` or `/* */` for comments

### C++
- `#include` for headers
- `std::cout` for output
- Pointers and references
- Use `//` or `/* */` for comments

---

## Stimulus-Based Code Questions

**Use STIMULUS for complex code requiring multiple questions:**

````
Type: STIMULUS
Prompt:
Analyze the following code and answer the questions that follow.

```python
class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance
    
    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            return True
        return False
    
    def withdraw(self, amount):
        if amount > 0 and amount <= self.balance:
            self.balance -= amount
            return True
        return False
```
---
Type: MC
Points: 6
Prompt:
What will `account.balance` be after this code executes?

```python
account = BankAccount(100)
account.deposit(50)
account.withdraw(30)
```

Choices:
- [ ] 100
- [x] 120
- [ ] 80
- [ ] 150
---
Type: MC
Points: 6
Prompt:
What does the `withdraw` method return if the amount exceeds the balance?

Choices:
- [ ] The remaining balance
- [ ] 0
- [x] False
- [ ] An error message
---
Type: ESSAY
Points: 12
Prompt:
In 5-8 sentences, explain how you would modify this class to prevent 
the balance from going negative and add a method to check the current balance.
````

---

## Common Mistakes to Avoid

### ❌ Don't Use Smart Quotes in Code

**Bad:**
````
```python
print("Hello")  # Curly quotes will break!
```
````

**Good:**
````
```python
print("Hello")  # Straight quotes work
```
````

---

### ❌ Don't Mix Code and Prose Without Clear Separation

**Bad:**
```
Calculate the sum using x = 5 and y = 10 and print(x + y)
```

**Good:**
```
Calculate the sum using the following code:

```python
x = 5
y = 10
print(x + y)
```
```

---

### ❌ Don't Assume Students Know All Syntax

**Provide context for unfamiliar syntax:**

```
Type: MC
Points: 8
Prompt:
The following code uses a list comprehension to create a new list:

```python
squares = [x**2 for x in range(5)]
```

What will `squares` contain?

Choices:
- [ ] [0, 1, 2, 3, 4]
- [x] [0, 1, 4, 9, 16]
- [ ] [1, 4, 9, 16, 25]
- [ ] [2, 4, 6, 8, 10]
```

---

## Assessment Balance for CS

**Recommended question mix for comprehensive CS quiz:**

- **30-40%** Code output/behavior prediction
- **20-30%** Syntax and language features
- **20-30%** Debugging and error identification
- **10-20%** Conceptual understanding (when to use what)
- **10-20%** Algorithm analysis or code writing (essay/FITB)

**Example 20-question quiz:**
- 8 MC on code output
- 5 MC on syntax/features
- 4 MC on debugging
- 2 FITB on code completion
- 1 Essay on algorithm analysis

---

## File Upload for Programming Projects

**Use when students submit working code files:**

```
Type: FILEUPLOAD
Points: 50
Prompt:
Upload your completed Python program: `calculator.py`

**Requirements:**
- Implement addition, subtraction, multiplication, division
- Handle division by zero with try/except
- Include a main() function that runs the program
- Follow PEP 8 style guidelines
- Include docstrings for all functions

**File format:** .py only
**Testing:** Your code will be run with test cases. Ensure it executes without errors.

**Grading criteria:**
- Functionality (30 pts): All operations work correctly
- Error handling (10 pts): Graceful handling of invalid input
- Code style (5 pts): PEP 8 compliance, readable variable names
- Documentation (5 pts): Clear docstrings and comments
```

---

## Summary

**Key principles for CS quizzes:**
✅ Use fenced code blocks with language tags  
✅ Preserve indentation exactly  
✅ Mix question types (output, syntax, debugging, concepts)  
✅ Use stimulus for complex code requiring multiple questions  
✅ Provide clear error messages when testing debugging skills  
✅ Balance recall questions with application/analysis  
✅ Use file upload for complete programming projects  

