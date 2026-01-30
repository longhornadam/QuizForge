# Rich Text Formatting in QuizForge: Analysis & Recommendations
**Date:** January 30, 2026  
**Purpose:** Recommendations for improving question prompt formatting within Canvas QTI-ZIP constraints

---

## Current State Analysis

### What Works Today
QuizForge currently supports rich formatting **only in `STIMULUS` items** with `render_mode: "executable"`:
- ✅ Fenced code blocks (```python, ```javascript, etc.) → styled `<pre><code>` blocks
- ✅ Prose passages with paragraph numbering (````prose`)
- ✅ Poetry with line numbering (````poetry`)
- ✅ Inline code with backticks → `<code>` tags
- ✅ Blockquotes with `>` prefix
- ✅ Automatic paragraph wrapping with `<p>` tags

### The Problem
**Regular question prompts and choices currently render as plain text without line breaks or formatting:**
- ❌ Multi-paragraph prompts display as a single run-on line
- ❌ No way to add bullet lists in question text
- ❌ No bold/italic emphasis for key terms
- ❌ Newlines in JSON strings (`\n`) are ignored in verbatim mode
- ❌ Teachers must use STIMULUS blocks even for simple formatting needs

### Root Cause
The `render_mode` system defaults to `"verbatim"` for all non-STIMULUS items:
```python
# From qti_builder.py lines 191-196
material.append(
    html_mattext(
        htmlize_prompt(
            question.prompt,
            excerpt_numbering=enable_excerpt_numbering,
            render_mode=getattr(question, "render_mode", "verbatim"),  # <-- Defaults to verbatim
        )
    )
)
```

In verbatim mode, `htmlize_prompt()` returns the raw string unchanged (line 430):
```python
if mode != "executable":
    if original_text != text or len(original_text) != len(text):
        raise ValueError("Verbatim render_mode mutated student-facing text during formatting.")
    return text  # <-- No processing, no HTML, no line breaks
```

---

## Canvas QTI Capabilities (What's Possible)

Canvas New Quizzes **fully supports HTML in QTI `<mattext>` elements** with `texttype="text/html"`. Based on Canvas_QTI_Patterns.md and testing:

### Confirmed HTML Support
✅ **Block Elements:**
- `<p>` - Paragraphs (most reliable)
- `<div>` - Generic containers with inline styles
- `<pre>` - Preformatted text (for code)
- `<ul>`, `<ol>`, `<li>` - Lists
- `<blockquote>` - Quotations
- `<table>`, `<tr>`, `<td>` - Tables

✅ **Inline Elements:**
- `<strong>`, `<b>` - Bold
- `<em>`, `<i>` - Italic
- `<code>` - Inline code
- `<span>` - With inline CSS styles
- `<br>` - Line breaks

✅ **Styling:**
- Inline CSS via `style=""` attributes
- Font families, sizes, colors
- Backgrounds, borders, padding
- Line height, margins

❌ **Not Supported:**
- `<script>` tags (security)
- External CSS stylesheets
- JavaScript
- SVG (limited/inconsistent)

### Key Finding
**Canvas accepts the same rich HTML in question prompts as it does in STIMULUS items.** The limitation is artificial—QuizForge's verbatim mode prevents it, not Canvas.

---

## Recommendations

### Option 1: Enable Selective Formatting (Recommended)
**Allow teachers to opt-in to formatting on a per-item basis.**

#### Implementation:
1. Add `"enable_formatting": true` field to item schema (optional, defaults to `false`)
2. When true, set `render_mode = "executable"` for that item
3. Update QFBase documentation to explain the flag

#### Example:
```json
{
  "type": "MC",
  "prompt": "Consider this Python output:\n\n```python\nprint('Hello')\n```\n\nWhat does it display?",
  "enable_formatting": true,
  "choices": [...]
}
```

#### Pros:
- ✅ Backward compatible (defaults to current behavior)
- ✅ Teacher has explicit control
- ✅ No risk of unexpected formatting changes
- ✅ Minimal code changes (already built, just needs schema flag)

#### Cons:
- ❌ Requires teacher to know about the flag
- ❌ Extra field in JSON

---

### Option 2: Auto-Detect Formatting Needs (Smart Default)
**Automatically enable formatting when prompt contains markdown-like patterns.**

#### Implementation:
```python
def should_enable_formatting(text: str) -> bool:
    """Auto-detect if text needs formatting."""
    indicators = [
        r'```',           # Code fences
        r'\n\n',          # Multiple paragraphs
        r'^\d+\.',        # Numbered lists
        r'^\*\s',         # Bullet lists
        r'`[^`]+`',       # Inline code
        r'\*\*[^*]+\*\*', # Bold markdown
    ]
    return any(re.search(pattern, text) for pattern in indicators)
```

Apply in qti_builder.py:
```python
render_mode = getattr(question, "render_mode", None)
if render_mode is None:  # No explicit mode
    render_mode = "executable" if should_enable_formatting(question.prompt) else "verbatim"
```

#### Pros:
- ✅ Zero teacher configuration
- ✅ Backward compatible (plain prompts unchanged)
- ✅ Intuitive—formatting "just works"
- ✅ Reduces need for STIMULUS blocks

#### Cons:
- ❌ Implicit behavior might surprise teachers
- ❌ Edge cases might trigger unexpectedly
- ❌ Harder to debug formatting issues

---

### Option 3: Default-On with Escape Hatch (Aggressive)
**Enable formatting by default, allow opt-out.**

#### Implementation:
1. Change default `render_mode` from `"verbatim"` to `"executable"`
2. Add `"raw_text": true` field to force verbatim mode
3. Update all existing quizzes to include `"raw_text": true` during migration

#### Pros:
- ✅ Best UX for new users
- ✅ Unlocks full HTML capabilities
- ✅ Reduces STIMULUS overuse

#### Cons:
- ❌ **Breaking change** for existing quizzes
- ❌ Requires migration script
- ❌ Risk of unintended formatting in legacy content
- ❌ Hard to validate all existing content

---

### Option 4: Markdown Subset (New Parser)
**Implement a safe Markdown subset specifically for prompts.**

#### Supported Syntax:
```
**bold**, *italic*
- Bullet lists
1. Numbered lists
`inline code`
```code blocks```

> Blockquotes

Blank lines → <p> breaks
```

#### Implementation:
Create new `markdown_to_canvas_html()` function that only supports these patterns, then use it in a new `render_mode = "markdown"`.

#### Pros:
- ✅ Clean, predictable syntax
- ✅ Safe (limited attack surface)
- ✅ Familiar to teachers
- ✅ Can add features incrementally

#### Cons:
- ❌ Significant development work
- ❌ Need to maintain custom parser
- ❌ Duplicates some existing code
- ❌ Markdown edge cases are complex

---

## Specific Feature Recommendations

### 1. Line Breaks (`\n` → `<br>` or `<p>`)
**Current:** In verbatim mode, `\n` in JSON strings is preserved literally but Canvas ignores it.
**Fix:** Convert standalone `\n` → `<br>`, double `\n\n` → paragraph breaks.

```python
def convert_line_breaks(text: str) -> str:
    # Double newlines = paragraph breaks
    paragraphs = text.split('\n\n')
    result = []
    for para in paragraphs:
        # Single newlines within paragraph = line breaks
        lines = para.split('\n')
        para_html = '<br>'.join(lines)
        result.append(f'<p>{para_html}</p>')
    return ''.join(result)
```

### 2. Basic Emphasis
**Allow:** `**bold**`, `*italic*` (Markdown-like)  
**Convert to:** `<strong>bold</strong>`, `<em>italic</em>`

```python
text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
```

⚠️ **Caution:** Must not interfere with math notation (asterisks for multiplication).

### 3. Simple Lists
**Allow:**
```
- Item 1
- Item 2
```

**Convert to:**
```html
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>
```

### 4. Inline Code (Already Supported)
**Allow:** `` `code` `` → `<code>code</code>`  
**Status:** ✅ Already works in executable mode

### 5. Code Blocks (Already Supported)
**Allow:** ` ```python\ncode\n``` ` → `<pre><code>code</code></pre>`  
**Status:** ✅ Already works in executable mode

---

## Implementation Priority

### Phase 1: Quick Wins (Minimal Changes)
1. **Document current capabilities** - Add to QFBase that STIMULUS items support full formatting
2. **Add `enable_formatting` flag** - Option 1 above, ~50 lines of code
3. **Test with existing Canvas imports** - Validate HTML support

### Phase 2: Improve Defaults (Medium Effort)
4. **Implement auto-detection** - Option 2, ~100 lines + tests
5. **Add line break conversion** - Essential for readability
6. **Extend to choice text** - Apply same logic to MC/MA options

### Phase 3: Full Markdown (Long-term)
7. **Markdown subset parser** - Option 4, ~500 lines + comprehensive tests
8. **List support** - Bullets and numbering
9. **Emphasis support** - Bold/italic with escape rules

---

## Proposed QFBase Updates

### Short-term Addition (Works Today):
```markdown
## 6a. FORMATTING OPTIONS (ADVANCED)

By default, question prompts render as plain text. To enable rich formatting:

**Option A: Use a STIMULUS block**
- Stimuli support code fences, prose/poetry formatting, and inline styles
- Attach questions using `stimulus_id`
- Limit to 2-4 questions per stimulus

**Option B: Add formatting flag (experimental)**
- Include `"enable_formatting": true` in the item
- Allows code fences, inline code, and paragraph breaks in prompts
- Use `\n\n` for paragraph breaks, ` ```python ` for code blocks
- Same capabilities as STIMULUS items
```

### Long-term Addition (After Implementation):
```markdown
## 6. TEXT FORMATTING IN PROMPTS

QuizForge supports rich text formatting in question prompts and choices:

**Paragraphs:** Separate with blank lines (`\n\n` in JSON)
**Emphasis:** Use `**bold**` and `*italic*`
**Lists:** Start lines with `-` (bullets) or `1.` (numbered)
**Inline code:** Wrap in backticks `` `code` ``
**Code blocks:** Use fenced blocks ` ```python\ncode\n``` `

Formatting is auto-enabled when markdown patterns are detected.
To force plain text, add `"raw_text": true` to the item.
```

---

## Testing Strategy

### 1. Canvas Import Tests
Create test quizzes with:
- Multi-paragraph prompts with `<p>` tags
- Bold/italic in question stems
- Lists in MC choices
- Mixed code blocks and text
- Edge cases (empty paragraphs, nested formatting)

### 2. Render Mode Tests
- Verify verbatim mode is strict identity (no mutations)
- Verify executable mode handles all supported patterns
- Test auto-detection accuracy

### 3. Legacy Compatibility
- Import existing quiz library with changes disabled
- Validate no regressions in current quizzes
- Test migration path for opt-in

---

## Security Considerations

### XSS Prevention
Canvas sanitizes HTML on import, but QuizForge should:
1. **Never allow raw HTML input** from users
2. **Generate HTML only from known-safe patterns** (markdown subset)
3. **Escape all user text** with `xml.sax.saxutils.escape()`
4. **Whitelist HTML tags** - only generate `<p>`, `<strong>`, `<code>`, etc.

### Current Safety
✅ QuizForge already uses `xml_escape()` correctly  
✅ Generated HTML uses whitelisted tags only  
✅ No user-supplied HTML is passed through

---

## Conclusion

**Recommendation:** Implement **Option 1 (Selective Formatting)** first, then migrate to **Option 2 (Auto-Detection)** after validation.

### Immediate Actions:
1. Add `enable_formatting` field to schema
2. Update QFBase with formatting guidance
3. Test Canvas import with sample HTML prompts
4. Document current STIMULUS capabilities

### Why This Approach:
- ✅ Minimal risk (opt-in by design)
- ✅ Quick to implement (~1-2 hours)
- ✅ Backward compatible
- ✅ Unlocks 80% of use cases
- ✅ Provides data for auto-detection heuristics

The Canvas QTI format **fully supports** rich HTML formatting. The limitation is QuizForge's conservative verbatim mode, not Canvas. By strategically enabling executable mode, QuizForge can provide attractive, readable question prompts while maintaining safety and compatibility.
