# MODEL SCOUT - PHASE 2 UI REDESIGN DOCUMENTATION

## Design Principle
**If a user cannot decide on a model within 30 seconds, the UI has failed.**

## Page Structure Overview

### 1. HOME PAGE (`/`) - "Find a Model"
**Primary Function**: Requirement-first model recommendation

**Sections** (5 total - within cognitive load limit):
1. **Header** (Sticky)
   - Logo
   - 3 primary actions: Find a Model, Compare Two, Explore Data
   
2. **Hero** (1-liner value prop)
   - Clear headline: "Find the Right AI Model"
   - One-sentence explanation
   
3. **Describe Your Needs** (Primary Interaction - ALWAYS VISIBLE)
   - Use case (2-line textarea)
   - Cost priority (3 options: low/medium/high)
   - Quality priority (3 options: low/medium/high)
   - Progressive disclosure: Latency & Context (collapsed)
   - Monthly budget slider ($10-$1000)
   - Usage level selector (low/medium/high)
   - Single CTA: "Get Recommendation"

4. **Recommendation Result** (Scannable hierarchy)
   - Model name (headline)
   - Why it fits (3 bullets max from reasoning)
   - Estimated cost (always visible, with assumptions)
   - Caveats (important limitations)
   - Data freshness (trust indicator)

5. **Alternative Models** (Collapsed by default)
   - "Why not other models?" expandable
   - Model name + reasons listed

**Cognitive Load**:
- Sections: 5 ✓
- Primary buttons: 1 (Get Recommendation) ✓
- Secondary buttons: 3 (navigation) ✓

**UX Rationale**:
- **Why requirement-first?** Users care about solving their problem, not browsing models
- **Why progressive disclosure?** Reduces form intimidation, most users don't need advanced options
- **Why collapsed alternatives?** Focused decision-making - show the answer first, explain later
- **Why slider for budget?** Visual, quick, no typing required
- **Why plain English?** "Low cost" is clearer than "minimize TCO"

---

### 2. COMPARE PAGE (`/compare`) - "Compare Two Models"
**Primary Function**: Side-by-side model comparison

**Sections** (4 total):
1. **Header** 
   - Back button
   - Page title
   
2. **Model Selection**
   - Two dropdowns (Model A, Model B)
   - Single CTA: "Compare Models"

3. **Verdict** (Plain English)
   - High-level summary (no jargon)
   - E.g., "Both models have similar performance. GPT-4o is more cost-effective."

4. **Side-by-Side Columns** (Vertical comparison)
   Each column shows:
   - Model name
   - Strengths (✓ icon, bullet list)
   - Weaknesses (derived from other model's strengths)
   - Cost per 1M tokens 
   - "Choose this if:" (plain English conditions)

5. **Key Tradeoffs** (Below columns)
   - 2-3 bullets summarizing main differences
   - E.g., "GPT-4o offers better reasoning, while Gemini provides longer context."

**NOT Shown**:
- ❌ Raw benchmark tables
- ❌ Dense comparison grids
- ❌ Charts/graphs (unless explicitly requested)

**UX Rationale**:
- **Why vertical?** Easier to scan than horizontal dense tables
- **Why strengths/weaknesses not scores?** Users don't care if MMLU is 85 vs 87, they care about "good at coding"
- **Why "Choose if"?** Decision framework, not just data
- **Why verdict first?** Answer the question immediately, then provide supporting detail

---

### 3. BENCHMARKS PAGE (`/benchmarks`) - "Explore Data"
**Primary Function**: Advanced exploration (for technical users)

**Sections** (Existing dashboard kept):
- Search bar
- Terminal feed (live logs)
- Source status
- Top models card
- Benchmark charts
- Cross-benchmark table

**Changes**:
- ✅ Marked as "Advanced" in navigation
- ✅ Not default landing page
- ✅ Benchmark tables COLLAPSIBLE by default
- ✅ "Strong/Moderate/Weak" labels added above raw scores

**UX Rationale**:
- **Why keep it?** Technical users still need detailed data
- **Why not primary?** Most users don't need this level of detail
- **Why collapsible tables?** Don't overwhelm casual users who accidentally land here

---

## Navigation Structure

### Primary Navigation (Max 3 items):
1. **Find a Model** (/)
   - Icon: Search
   - Default landing page
   
2. **Compare Two** (/compare)
   - Icon: GitCompare
   - Side-by-side comparison

3. **Explore Data** (/benchmarks)
   - Icon: BarChart3
   - Advanced benchmarks view

**NOT in Primary Nav**:
- Live feed status
- Radar charts
- PRS scores
- Historical data

**UX Rationale**:
- **Why 3 items?** Decision paralysis research shows 3-4 options is optimal
- **Why these 3?** Cover the 3 core user intents:
  1. "What model should I use?"
  2. "Which of these two is better?"
  3. "Show me the data"
- **Why no leaderboard?** Leaderboards imply "best overall" - we explicitly avoid this

---

## Component-Level Changes

### Form Components
**Before**: Long forms, technical terms
**After**: 
- Max 2-line inputs
- Dropdowns with plain English (not "low/medium/high quality" but "basic/good enough/best available")
- Sliders for numerical values
- Progressive disclosure for optional fields

### Results Display
**Before**: Dense benchmark tables upfront
**After**:
- Headline answer first
- 3-bullet reasoning
- Cost always visible (with assumptions stated)
- Raw data hidden behind "Show details" or tooltips

### Comparison UI
**Before**: Horizontal dense grids
**After**:
- Vertical cards (one per model)
- Strengths/weaknesses extracted from benchmarks
- "Choose if..." decision framework
- Plain-English verdict

### Trust Indicators
**Always Visible**:
- Data freshness ("Updated 3 days ago")
- Source count ("Based on 4 benchmark sources")
- Confidence level ("high/medium/low confidence")
- Incomplete data warnings

**Format**:
```
📊 Based on 4 benchmark sources · Updated 3 days ago
```

---

## What We Explicitly Did NOT Add

❌ **Charts** - Only if explicitly requested
❌ **Leaderboards** - Implies "best overall"
❌ **Auto-scrolling dashboards** - Cognitive overload
❌ **Real-time animations** - Distracting
❌ **Hidden logic** - All reasoning is transparent
❌ **"Best model overall"** language - Violates honesty principle

---

## Before/After Comparison

### User Flow: "I need a model for my chatbot"

#### BEFORE (Old UI):
1. Land on dashboard with charts
2. Search for "GPT-4"
3. See terminal logs
4. See raw benchmark scores
5. See radar chart
6. See table with 20 metrics
7. ??? What should I pick?

**Time to decision**: 2-5 minutes (assuming user understands benchmarks)

#### AFTER (New UI):
1. Land on "Describe Your Needs"
2. Type "chatbot for customer support"
3. Select "low cost" + "medium quality"
4. Set budget to $50/month
5. Click "Get Recommendation"
6. See: "Recommended: GPT-4o-mini"
7. Read: "Very low cost, fast responses, good for high-volume"
8. See: "$8/month estimated"
9. ✅ Decision made

**Time to decision**: 30 seconds

---

## Typography & Visual Hierarchy

### Headline Sizes:
- Page title: `text-4xl` (36px)
- Section headers: `text-xl` (20px)
- Subsections: `text-sm font-semibold` (14px)
- Body: `text-sm` (14px)
- Metadata: `text-xs` (12px)

### Color Usage:
- **Primary** (brand color): CTAs, model names, key metrics
- **Secondary** (success): Recommended model, "within budget"
- **Muted**: Supporting text, metadata
- **Destructive**: Over budget, errors
- **Warning**: Caveats, incomplete data

### Spacing:
- Between sections: `mb-8` (32px)
- Between cards: `gap-6` (24px)
- Internal card padding: `p-6` (24px)
- Between form fields: `space-y-6` (24px)

**UX Rationale**:
-  **Why large headlines?** Scannability
- **Why consistent spacing?** Reduces visual noise
- **Why muted for metadata?** De-emphasizes non-critical info

---

## Mobile Responsiveness

All pages designed mobile-first:
- Form inputs stack vertically
- Side-by-side becomes stacked cards
- Sticky header remains
- Text remains readable (minimum 14px)
- Touch targets minimum 44x44px

---

## Accessibility Considerations

- ✅ Semantic HTML (h1, h2, p, ul, etc.)
- ✅ ARIA labels on interactive elements
- ✅ Keyboard navigation (Tab order logical)
- ✅ Focus indicators visible
- ✅ Color contrast meets WCAG AA
- ✅ No information conveyed by color alone

---

## Testing Checklist

### Cognitive Load Test:
- [ ] Can user find "Get Recommendation" in 3 seconds?
- [ ] Are there more than 5 visible sections? (FAIL if yes)
- [ ] Are there more than 3 primary buttons? (FAIL if yes)

### Decision Speed Test:
- [ ] Can a new user get a recommendation in under 60 seconds?
- [ ] Can user understand why Model A beats model B in under 30 seconds?

### Clarity Test:
- [ ] Does any text use ML jargon without explanation?
- [ ] Are benchmark scores shown before plain-English summary? (FAIL if yes)
- [ ] Is cost estimate missing assumptions? (FAIL if yes)

---

## Implementation Notes

### API Integration:
- `POST /api/v2/analyst/recommend` - Powers Home page
- `POST /api/v2/analyst/compare` - Powers Compare page
- `GET /api/v2/analyst/models` - Populates model dropdowns

### State Management:
- Local state (useState) for all forms
- No global state needed
- Form validation inline

### Performance:
- API calls only on user action (no auto-fetch)
- Results cached in component state
- No polling/websockets

---

## Success Metrics

**Primary**:
- Time to first recommendation: < 60 seconds
- Time to comparison decision: < 30 seconds

**Secondary**:
- % users who expand "Why not alternatives": ~30%
- % users who set advanced options: ~20%
- % users who visit /benchmarks: ~10%

**Quality**:
- No "confused" user feedback
- No "too technical" feedback
- Increased "clear" / "helpful" feedback

---

## Future Enhancements (NOT in Phase 2)

- [ ] Save favorite models
- [ ] Export comparison as PDF
- [ ] Email recommendation summary
- [ ] Model history tracking
- [ ] Custom requirement templates

These are EXPLICITLY deferred to keep Phase 2 focused on core clarity.
