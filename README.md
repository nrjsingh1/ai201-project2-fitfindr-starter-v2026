# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a plain-English thrift request like `'vintage graphic tee under $30'`
and searches 40 secondhand listings from Depop, thredUp and Poshmark, filtering
by price ceiling and size and ranking by keyword match. It picks the top
listing, then asks the model for one or two outfits built from pieces already in
the user's wardrobe (or general styling advice if the wardrobe is empty), and
finally writes a short caption the user could post about the find. If nothing
matches, it stops before calling the model and says which part of the request
(the words, the size or the price) to change.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings in `data/listings.json` by price and size, then ranks what's left by how many words from `description` appear in each listing's `title`, `description` and `style_tags`. It does not call the model.
- **Inputs:**
  - `description` (str): keywords such as `"vintage graphic tee"`. Matching ignores case. One point per query word found in the title, description or tags. Words under 3 characters are ignored.
  - `size` (str or None): `None` skips size filtering. Otherwise the listing's `size` is split on `/`, spaces and brackets into tokens, and the listing matches if any token equals the requested size, ignoring case. `"M"` matches `S/M` and `M/L` but not `XL (oversized)`, and `"S"` never matches `US 9`. Shoe sizes are compared as `US <n>` (`"8"` matches `US 8`, not `US 8.5`). Waist sizes are compared as `W<n>` (`"W30"` matches `W30 L30`). `One Size` listings pass every size filter.
  - `max_price` (float or None): inclusive ceiling. `None` skips price filtering.
- **Returns:** a `list[dict]` of listing dicts, highest keyword score first, at most `config.SEARCH_RESULT_LIMIT` (10). Each dict is the listing unchanged, with keys `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str **or None**) and `platform` (str). Listings with a score of 0 are dropped. Ties keep file order.
- **When it has nothing:** returns an empty list `[]`. It never returns `None` and never raises. This is what the loop branches on.

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for one or two outfits built around the thrifted item. When the wardrobe has items, the outfits use pieces the user already owns.
- **Inputs:**
  - `new_item` (dict): one listing dict from `search_listings`, with the same keys as above.
  - `wardrobe` (dict): `{"items": [...]}`. Each item has `id` (str), `name` (str), `category` (str: tops / bottoms / outerwear / shoes / accessories), `colors` (list[str]), `style_tags` (list[str]) and `notes` (str or None). `items` may be an empty list.
- **Returns:** a non-empty `str` of plain text with 1–2 outfit suggestions. With a wardrobe, each outfit names specific pieces from it by `name`, so it never invents clothes the user doesn't own.
- **When it has nothing:** if `wardrobe["items"]` is empty or missing, it still returns a non-empty `str`: general styling advice for the item (what kinds of pieces, colors and vibe go with it). It never returns `""` and never raises for an empty wardrobe. If the model can't be reached, `ModelUnavailable` propagates up to the loop.

### `create_fit_card`

- **What it does:** Asks the model, through `generate()`, for a short social-media caption about the find that sounds like a real post, not a product description.
- **Inputs:**
  - `outfit` (str): the string `suggest_outfit` returned.
  - `new_item` (dict): the same listing dict that was passed to `suggest_outfit`.
- **Returns:** a `str` caption of 2–4 sentences. It mentions the item's `title`, `price` (as `$NN`) and `platform` exactly once each, and describes the vibe of the outfit specifically. Captions vary between runs (`TEMPERATURE` = 0.9).
- **When it has nothing:** if `outfit` is empty or only whitespace, it skips the model call and returns the fixed string `"Couldn't write a fit card: no outfit suggestion was provided for <title>."`. It never returns `""` and never raises for an empty outfit.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that names what the user could change (broader words, a different size, a higher price ceiling), and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, put the first result in `session["selected_item"]` and go on to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** with regex, not a model call. A `$<number>` (optionally after "under", "below" or "up to") becomes `max_price`. `size <X>` becomes `size`. Whatever text is left becomes `description`. Regex costs nothing and gives the same answer every time. The tradeoff is that it misses phrasing it wasn't written for: "under thirty dollars" sets no price ceiling.

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` → **branch** → `selected_item` → `outfit_suggestion` → `fit_card`. `error` is set only if the run stops early. When it is, every field after the stopping point stays `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Grab that butterfly baby tee, it is a great find for eighteen dollars.   Outfit one leans into that nostalgic …
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Scored this Y2K baby tee with the cutest butterfly print for just $18 on depop, and I'm obsessed. I've been li…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Grab that butterfly baby tee, it is a great find for eighteen dollars. 

Outfit one leans into that nostalgic streetwear contrast. Pair the baby tee with the baggy straight-leg jeans, dark wash on the bottom. Throw the vintage black denim jacket over top to tie the dark tones together, and step into the chunky white sneakers. Add the black crossbody bag for a complete Y2K street look.

Outfit two mixes the cute graphic top with structured earth tones. Tuck the baby tee into the wide-leg khaki trousers. Cinch the waist with the brown leather belt, and finish the outfit with the black combat boots to add a little edge.

  Fit card: Scored this Y2K baby tee with the cutest butterfly print for just $18 on depop, and I'm obsessed. I've been living in it lately, whether I'm styling it with baggy dark-wash denim and a vintage jacket for that ultimate nostalgic streetwear contrast, or dressing it down with edgy khaki trousers and combat boots 🦋

1 model calls this session, 1 served from cache, 238 prompt + 73 output tokens
```

The same loop with a query the data can't match. It stops at the branch, makes
no model calls, and `fit_card` stays `None`:

```
$ python app.py ask 'designer ballgown size XXS under $5'
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: stopping before suggest_outfit

  Nothing in the listings matched description 'designer ballgown', size XXS, under $5.
Things to change: try broader words — 'jacket' finds more than 'cropped corduroy jacket'; drop the size, or try a neighbouring one; raise the price ceiling above $5.

0 model calls this session
```

**The three tools, tested one at a time**

`search_listings`, a match and the empty case:

```
$ python -c "from tools import search_listings; print([(l['title'], l['price']) for l in search_listings('graphic tee', max_price=30)])"
[('Y2K Baby Tee — Butterfly Print', 18.0), ('Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('Mesh Long-Sleeve Top — Black', 15.0), ('Vintage Band Tee — Faded Grey', 19.0), ('Low-Rise Cargo Pants — Khaki', 27.0), ('Oversized Crewneck Sweatshirt — Vintage Navy', 20.0), ('Vintage Graphic Hoodie — Faded Black', 26.0)]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

Every result is ≤ $30. The cargo pants match because their description says
"tee". Plain keyword search counts that.

`suggest_outfit`, with the example wardrobe and then an empty one:

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit one: Wear the vintage Levi's 501 jeans with the white ribbed tank top tucked in. Add the brown leather belt, the slightly cropped vintage black denim jacket on top, and finish with the chunky white sneakers and black crossbody bag for an easy, classic streetwear look.

Outfit two: Pair the vintage Levi's 501 jeans with the oversized grey crewneck sweatshirt worn loose and relaxed. Cinch the waist with the brown leather belt, and step into the black combat boots. Grab the black crossbody bag to complete this cozy, casual fit.

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Here is how you can style those vintage Levi's 501s. 

Outfit one leans into a casual streetwear vibe. Pair the medium wash denim with an oversized, graphic crewneck sweatshirt in heather gray or forest green. Finish it off with chunky retro sneakers, like white-and-red leather runners, and a canvas tote bag. 

Outfit two is a classic, effortless look. Tuck a fitted ribbed tank top in black or white into the waistband, and layer an unbuttoned oversized linen button-down shirt over top in olive or beige. Add a worn brown leather belt and well-loved leather loafers or flat slides to keep the vintage energy grounded and cool.
```

`create_fit_card`, run three times on the same item, then with an empty outfit:

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored the ultimate everyday uniform with these vintage Levi's 501 jeans for only $38. They have that perfectly broken-in medium wash that looks effortless paired with crisp white sneakers for a casual weekend coffee run. Snag them now over on my depop before I change my mind and keep them. 👖

Scored the ultimate everyday pair with these vintage Levi's 501 jeans for only $38. I'm keeping the vibe super effortless by pairing them with fresh white sneakers for running weekend errands. Grab them over on my depop before I change my mind and keep them for myself 👖✨

Nothing beats the effortless look of a worn-in medium wash paired with crisp white sneakers for that ultimate effortless 90s off-duty vibe. I just scored these vintage Levi's 501 jeans on depop for $38 and I am never taking them off 🤌✨

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
Couldn't write a fit card: no outfit suggestion was provided for Vintage Levi's 501 Jeans — Medium Wash.
```

The three captions differ, though the first two are close. `TEMPERATURE` is
0.9 and `create_fit_card` passes `cache=False`, so each run is a real call.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

I used Claude Code (Opus 5.5) throughout this unit. It ran the starter, wrote
the tool spec, built the tools and wired the loop from my milestone
instructions. I also asked it to draft acceptance criteria 3–5 and the reasons
under all five, even though the milestone says to write those myself, so I need
to read them closely and be ready to defend or revise them in unit 4.

**Moment 1**

- *What I asked for:* wire `run_agent` in `agent.py` so a full query runs all three tools through the session, and an impossible query stops early.
- *What came back:* the loop ran, but testing the example queries showed `parse_query('platform sneakers size 8')` returned `size: None` and left "size 8" inside the description. The size regex only accepted `US 8`, not a bare number, so the size filter was silently skipped. The trace also labelled the search step "via MCP" even though the MCP tool wasn't registered yet and every call was falling back to the local function.
- *What I changed:* the size regex now accepts a bare number (`size 8` → `'8'`, which `search_listings` treats as `US 8`, matching the Tool Inventory). The MCP wrapper is gone for unit 3, so the loop calls `search_listings` directly and the trace says what really happened.

**Moment 2**

- *What I asked for:* build `search_listings` to my Milestone 2 spec and test it from the terminal.
- *What came back:* the size rules all held (`M` matches `S/M`, `S` doesn't match `US 9`, `8` doesn't match `US 8.5`), but `'graphic tee', max_price=30` also returned low-rise cargo pants and a crewneck sweatshirt. Checking why: the cargo pants' description contains the word "tee" and the sweatshirt's contains "graphics", and my spec says to search descriptions.
- *What I changed:* I kept the behaviour because it is what the spec says, and noted it under Sample Run as a known weakness of plain keyword search. It is the first thing to look at in unit 4 if criterion 1 or result relevance comes up short.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

`search_listings` now runs on an MCP server. `mcp_server.py` registers it with
the same three typed inputs as the Tool Inventory (`description` string,
`size` optional string, `max_price` optional number) and a description that
states the size-matching rule, that prices are in US dollars, inclusive, and
that no match returns `[]`. `python mcp_client.py` lists the tool with exactly
those types. In `agent.py::run_agent`, the direct `search_listings(...)` call
became `call_tool("search_listings", {...})`. Nothing else in the loop changed.

Nothing behaved differently. Before swapping, I called both paths on the same
three inputs (`'vintage graphic tee'` ≤ $30, `'designer ballgown'` XXS ≤ $5,
`'sneakers'` size 8) and compared with `==`. The results were identical:
10, 0 and 1 listings. The empty case still comes back as a list `[]`, not
`None`, so the branch still fires. A full query picks the same item as in unit 3
(`lst_002`, Y2K Baby Tee, $18). The only cost is speed: each call starts the
server, asks, and stops it again.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
