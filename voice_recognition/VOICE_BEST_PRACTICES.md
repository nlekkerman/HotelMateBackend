# 🗣️ Voice Command Best Practices

## What to Say for Best Results

### ✅ Good Examples

**Simple counts:**
- "Count **Budweiser** seven cases"
- "**Heineken** count twelve bottles"
- "**Guinness draught** three kegs"

**With units:**
- "Count **Budweiser** three cases six bottles"
- "**Coors** two kegs minus five pints"
- "**Bulmers** five cases"

**Natural language:**
- "I have **Smithwicks** twelve bottles"
- "There are **Corona** twenty four"
- "Got **Heineken zero** six bottles"

---

## How the Parser Works

### 1. Action Keywords (Can Be Anywhere!)
- ✅ "**count** budweiser 7" 
- ✅ "budweiser **count** 7"
- ✅ "budweiser 7 **count**"
- ✅ "**I have** budweiser 7"
- ✅ "**there are** 7 budweiser"

### 2. Brand Name (Most Important!)
Say the **brand name clearly**:
- ✅ "budweiser" → matches "Budweiser Bottle"
- ✅ "bud" → matches "Budweiser Bottle"  
- ✅ "heineken" → matches "Heineken Bottle"
- ✅ "heiny" → matches "Heineken Bottle"

**You DON'T need to say "bottle" or "draught"** - the backend knows what products exist!

### 3. Quantities
- Numbers: "seven", "twelve", "twenty four"
- Decimals: "five point five"
- Cases + bottles: "three cases six bottles"
- Kegs + pints: "two kegs twelve pints"

### 4. Filler Words (Ignored)
These words are automatically removed:
- "umm", "uh", "ok", "so"
- "I think", "what is", "how many"
- "but", "why", "is it"

---

## Examples from Real Use

### Your Example:
**You said:** `"But why is it bottle, count? Three cases, two bottles."`

**Problem:** Only "bottle" remains after removing filler words - too generic!

**Better ways to say it:**
- "**Budweiser** count three cases two bottles"
- "Count **budweiser bottle** three cases two bottles"
- "**Bud** three cases two bottles count"

### Why It Matters:
- ❌ "bottle" → Too generic, could match 20+ items
- ✅ "budweiser" → Specific, matches exactly one item
- ✅ "bud bottle" → Even more specific

---

## Tips for Clear Commands

1. **Start with the brand name** (most reliable):
   - "Budweiser count seven cases"
   
2. **Or end with the brand name**:
   - "Count seven cases budweiser"

3. **Include action keyword somewhere**:
   - "count", "purchase", "waste", "have", "got"

4. **Speak numbers clearly**:
   - "three" not "tree"
   - "five" not "fife"

5. **Avoid too much filler**:
   - ✅ "Count budweiser seven"
   - ❌ "Um okay so like I think maybe budweiser is seven"

---

## What Gets Recognized

### Brand Names (Full or Partial):
- budweiser, bud, budwiser
- heineken, heiny, heine
- smithwicks, smithix
- guinness, guiness
- bulmers, bulmer
- corona
- coors, course

### Packaging (Optional):
- bottle, bot, botle
- draught, draft, tap
- can, tin
- pint, pt

### Units:
- cases, case, cs
- bottles, bottle, btl
- kegs, keg
- pints, pint, pt
- dozen

---

## Summary

**For your "Budweiser bottle 3 cases 2 bottles" example:**

✅ **Say:** "Budweiser count three cases two bottles"  
✅ **Say:** "Count budweiser three cases two bottles"  
✅ **Say:** "Bud count three cases two bottles"  

❌ **Avoid:** "But why is it bottle count three cases two bottles"

**Key rule:** Always include the brand name (budweiser, heineken, etc.) - not just "bottle"!
