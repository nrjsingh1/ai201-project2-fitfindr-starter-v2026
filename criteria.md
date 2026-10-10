# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Not 5 of 5, because two layers can fail on a query that does have a match.
Parsing is regex, so phrasing it wasn't written for ("under thirty dollars",
"medium") goes through unparsed or ends up in the description. Search is
plain keyword overlap with no synonyms, so "tshirt" won't find "tee". The two
model calls can also fail on their own. One miss in five allows for that.
More than one would mean the search itself is broken.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never reaches the model. It is regex, a filter over a local JSON
file, and one `if not results:` check, all deterministic, so the same query
gives the same result every time. Missing even once would mean the branch is
wrong, not unlucky. The message is built from the parsed query, so it always
names at least the description and whichever size or price was set.

---

## 3. The item search found is the item the next tools received

For 5 queries that match at least one listing, the `id` in
`session["selected_item"]` equals `session["search_results"][0]["id"]`, and
the trace shows that same `id` in the inputs to both `suggest_outfit` and
`create_fit_card`: 5 of 5 tries.

**Why this target:**
Passing one dict from step to step involves no model and no randomness, so
anything under 5 of 5 is a real bug, such as a variable overwritten between
steps or a tool re-running search, not noise. I check the `id` and not the
title because titles are not guaranteed unique, and I use the trace because it
shows what each tool actually received, not what the session says it should
have received.


---

## 4. The fit card is a usable caption for that specific item

For 5 queries that select 5 different listings, at least 4 of the 5 fit
cards are 2–4 sentences long (counting `.`, `!` and `?` endings), contain the
item's price written as `$` plus the number (e.g. `$24`), and contain its
platform name (`depop`, `thredUp` or `poshmark`, case-insensitive). No two of
the 5 cards start with the same first sentence.

**Why this target:**
The words are supposed to vary at `TEMPERATURE = 0.9`, so the criterion checks
what has to be true whatever the wording: right length, right price, right
platform. 4 of 5 and not 5 of 5 because a model given the price in the prompt
still sometimes leaves it out or runs long, and the prompt can't force it.
The no-repeated-opening rule has no slack: identical openings across different
items would mean the cache is on or the prompt ignores the item.

> **Revised in unit 4:** For 5 queries that select 5 different listings, at
> least 4 of the 5 fit cards are 2–4 sentences long (counting `.`, `!` and `?`
> endings), contain the item's price as `$` plus the number, contain its
> platform name, **and are written as the buyer, not the seller**: no card
> says or implies the poster is selling the item. Seller phrases include
> "just listed", "up on my depop", "live on my…", "available now",
> "parting with", "my poshmark", "before I change my mind", and "if you want
> to snag it". No two of the 5 cards start with the same first sentence.
> Target unchanged: 4 of 5 cards per try, in 5 of 5 tries.
>
> **Why revised:** the original measured the wrong thing. Its heading
> promises "a usable caption", but every check is about format, so a card
> that tells the shopper's friends the shopper is *selling* the jacket passes
> all of them. The before run proves it: every try passed, yet 26 of the 65
> cards in that run are written as the seller ("Finally parting with this 90s
> leather bomber… because my closet is overflowing"). Those cards can't be
> posted by the person the app is for. The revision adds one check, scored in
> `score_eval.py::seller_voice`, and **raises** the bar. The target number
> stays where it was.

## 5. The search respects the price ceiling

For 5 queries written with `under $N` (e.g. `'denim jacket under $50'`),
`session["parsed"]["max_price"]` equals N, and every listing in
`session["search_results"]` has `price` ≤ N: 5 of 5 queries, with zero
over-budget listings across all results.

**Why this target:**
A shopper who says "under $30" and gets shown a $45 jacket stops trusting
every other result. Both halves, the regex that pulls out N and the numeric
filter, are deterministic, so there's no room for a miss. Checking `parsed`
as well as the results catches the quiet failure where the price is never
parsed, the filter is skipped, and cheap items happen to come back anyway.
Spelled-out prices ("thirty dollars") are a known parser gap, written up in
the README, and deliberately not part of this test.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
