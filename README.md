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
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item is the item passed on (by id) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2-4 sentences, $price, platform | 4 of 5 cards, no repeat opening | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Search respects the price ceiling | 5 of 5 queries | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

How each try was scored: `python score_eval.py --label before` runs
`run_eval.py::main` unchanged (14 scenarios from `scenarios.py`, 5 tries each,
cache off, 132 real model calls). It then applies each criterion in
`criteria.md` to those same sessions in code, so every try is judged the same
way. Full output: `results/run_2026-10-09_2133_before.md`. Verdicts and the
reason for every try: `results/score_before.md`.

For criteria 1–3 a try is one run of that criterion's scenario. Criteria 4 and
5 are each written over five different queries, so a try is the k-th run of
all five: for criterion 4, 4+ of the 5 cards must pass with no repeated
opening; for criterion 5, all 5 queries must pass. Before trusting 25/25, I
checked that the 5 cards for the same item were 5 different texts, and that
the scorer flags a 1-sentence card, a missing price, a wrong `id` in the
trace and an over-budget listing when given them on purpose.

**Real output from one try** (try 1 of each; loop `agent.py::run_agent`,
search over MCP from `mcp_server.py::search_listings`, outfit
`tools.py::suggest_outfit`, card `tools.py::create_fit_card`):

*Criterion 1: matching query completes* (`vintage graphic tee under $30`)

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: lst_002 · Y2K Baby Tee — Butterfly Print ($18, depop)
[4] suggest_outfit
      in:  lst_002 · Y2K Baby Tee — Butterfly Print ($18, depop)
      out: For a balanced Y2K streetwear look, pair the butterfly baby tee with the baggy straight-leg jeans, dark wash. …
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  lst_002 · Y2K Baby Tee — Butterfly Print ($18, depop)
      out: Obsessed with this Y2K baby tee with the cutest butterfly print, scoring it for just $18 over on depop. I've b…

Fit card: Obsessed with this Y2K baby tee with the cutest butterfly print, scoring it for just $18 over on depop. I've been wearing it non-stop with baggy dark wash denim and chunky sneaks for that effortless off-duty streetwear vibe.
```

*Criterion 2: impossible query stops* (`designer ballgown size XXS under $5`)

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: stopping before suggest_outfit

session["error"]: Nothing in the listings matched description 'designer ballgown', size XXS, under $5.
Things to change: try fewer words — 'ballgown' alone finds more than 'designer ballgown'; drop the size, or try a neighbouring one; raise the price ceiling above $5.
session["fit_card"]: None
```

*Criterion 3: state* (`chunky knit cardigan`). `lst_008` is `search_results[0]`,
`selected_item`, and the input to both later tools:

```
[1] parse_query
      in:  chunky knit cardigan
      out: description='chunky knit cardigan', size=None, max_price=None
[2] search_listings (via MCP)
      in:  description='chunky knit cardigan', size=None, max_price=None
      out: 3 items: Knit Cardigan — Chunky Brown, Platform Sneakers — White Chunky Sole, Vintage Knit Vest — Argyle Brown/Cream
      →    3 match(es)
[3] select_item
      out: lst_008 · Knit Cardigan — Chunky Brown ($35, depop)
[4] suggest_outfit
      in:  lst_008 · Knit Cardigan — Chunky Brown ($35, depop)
      out: Outfit One: Earth Tone Comfort Layer the chunky brown knit cardigan over the white ribbed tank top. Pair them …
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  lst_008 · Knit Cardigan — Chunky Brown ($35, depop)
      out: Obsessed with this chunky brown knit cardigan I just dropped on depop for $35! It’s giving the ultimate cozy e…
```

*Criterion 4: fit cards for 5 different listings*:

```
[track jacket]
Found the ultimate 90s track jacket and couldn't wait to style it two ways, from baggy denim streetwear to crisp khaki smart-casual. Grab it on Poshmark for just $45 before I change my mind and keep it in my own rotation. 🧥✨

[silk slip dress]
Still obsessed with this 90s silk slip dress I just scored for only $30. Today I'm channeling total indie-sleuth energy by layering it under an oversized crewneck with combat boots, then switching it up tomorrow with a white tank and a cropped denim jacket for that ultimate grunge-meets-streetwear aesthetic. Find it live on my Depop right now 🥀

[platform sneakers]
Just scored these chunky platform sneakers for $48 on poshmark and I'm obsessed with how they pull together a relaxed Y2K streetwear vibe. I've already styled them two ways: first with baggy denim and a vintage jacket, and then dressed up a bit with wide-leg trousers and a cropped zip hoodie.

[corduroy pants]
Found these dreamy rust corduroy wide-leg pants on Depop for just $32 and I am obsessed. I've been styling them two ways: either leaning into a retro coffee run vibe with a tucked-in white tank and denim jacket, or keeping it cozy with an oversized grey crewneck and combat boots.

[leather bomber]
Finally parting with this 90s leather bomber for $75 on depop because my closet is overflowing. It goes with literally everything, whether you're leaning into heavy 90s grunge with a cropped hoodie and combat boots, or playing with minimal textures by throwing it over a ribbed tank and khaki trousers. 🧥
```

*Criterion 5: price ceiling*. Trace for the boundary case, where the $35
cardigan is kept by "under $35":

```
[1] parse_query
      in:  cardigan under $35
      out: description='cardigan', size=None, max_price=35.0
[2] search_listings (via MCP)
      in:  description='cardigan', size=None, max_price=35.0
      out: 1 items: Knit Cardigan — Chunky Brown
      →    1 match(es)
```

Result prices for all five queries. Search is deterministic (no model), so I
re-ran it through `mcp_client.call_tool` to list the prices, which the run
file doesn't print:

```
denim jacket under $50: prices [42.0, 38.0, 45.0, 24.0, 33.0, 30.0, 27.0] -> max 45.0 <= 50
graphic tee under $20: prices [18.0, 15.0, 19.0, 20.0] -> max 20.0 <= 20
cardigan under $35: prices [35.0] -> max 35.0 <= 35
boots under $45: prices [44.0] -> max 44.0 <= 45
flannel shirt under $25: prices [22.0, 20.0, 18.0] -> max 22.0 <= 25
```

**Noticed, but not measured by any criterion:** several fit cards speak as the
*seller* ("Finally parting with this 90s leather bomber… because my closet is
overflowing", "I just dropped on depop", "Grab it on Poshmark… before I change
my mind"), but the user is the *buyer*. And `chunky knit cardigan` also returns
Platform Sneakers ("chunky sole"), which is keyword overlap again.

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
| 1 | A matching query completes all three tools and returns a fit card | 4 of 5 | **MET (5/5)** | `session["error"]` was `None` and `fit_card` was a real caption in all 5 tries (`score_eval.py::check_1`). |
| 2 | An impossible query stops before `suggest_outfit` with a message naming what to change | 5 of 5 | **MET (5/5)** | In all 5 tries: `search_results == []`, no `suggest_outfit` step in the trace, `outfit_suggestion` and `fit_card` both `None`, and `error` contains "Things to change". |
| 3 | The `id` in `selected_item` equals `search_results[0]`'s and is what the trace shows going into both later tools | 5 of 5 | **MET (5/5)** | `lst_008` in all three places, in all 5 tries (`check_3` reads the trace's `in:` lines). |
| 4 | Fit card: 2–4 sentences, `$price`, platform, no repeated opening (4 of 5 cards) | 4 of 5 cards, 5 of 5 tries | **MET (5/5)** as written | All 25 cards passed every check. Read plainly, this verdict is misleading. See the revision and the miss below. |
| 4 (revised) | The same, **plus written as the buyer, not the seller** | 4 of 5 cards, 5 of 5 tries | **MISSED (0/5)** | Re-scored the *same* before run (no new calls): `python score_eval.py --rescore results/run_2026-10-09_2133_before.md --label before_revised4`. Only 2–3 of 5 cards pass in each try. |
| 5 | `under $N` parses to `max_price == N` and no result costs more than N | 5 of 5 queries, 5 of 5 tries | **MET (5/5)** | All 25 query-runs parsed N exactly. The highest result price never went over N; the $35 cardigan and the $20 tee sat exactly at the ceiling and were kept. |

**Diagnoses**

*Criterion 4 (revised): MISSED, 0 of 5 tries.*

- **Where:** the model's output, from `tools.py::create_fit_card`. Not a tool
  bug, the branch or the session. The trace shows the right item (`lst_004`,
  `lst_013`…) going into `create_fit_card` every time, and every card names
  that item, its price and its platform correctly. What's wrong is who the
  card says the poster is.
- **Mechanism:** the prompt never says the poster *bought* the item. It says
  "a caption for a social media post about this thrift find", gives
  `Platform: depop`, and requires "the platform exactly once". It even
  describes the outfit as "How *they're* styling it", which leaves the poster's
  identity open. On Depop, Poshmark and thredUp, the most common post that
  names an item, its price and the platform is a sale listing, so at
  temperature 0.9 the model often fills the gap with a seller: "It's up on my
  Poshmark for $45 if you want to make it yours", "Snag it on my depop before I
  change my mind". Some cards switch halfway through ("Just scored this… It's
  up on my Poshmark"), which shows the model taking the two readings in turn
  rather than holding one view.
- **The numbers:** 26 of all 65 cards in the before run are in seller voice,
  spread across every scenario that writes a card. In the five criterion-4
  scenarios: track jacket 5/5, leather bomber 3/5, silk slip dress 2/5,
  corduroy pants 2/5, platform sneakers 0/5.

*The pattern.* It's one problem, not five. The seller voice shows up in all
13 scenarios that produce a card, so it isn't one bad item. It isn't the
platform either: Poshmark items range from 5/5 (track jacket) to 0/5
(sneakers, boots). It isn't the empty wardrobe or the price ceiling path. The
only thing every case shares is the `create_fit_card` prompt. One missing line
in one prompt explains all 26.

*Were my targets low?* Partly, yes. Criteria 2, 3 and 5 test deterministic
code (the branch, a dict passed through the session, a regex and a `<=`). Once
that code was right, 5 of 5 was all but guaranteed. They prove the code works;
they were never going to be close. Criterion 1's 4 of 5 was loose: no try failed
for any reason, so it could be 5 of 5. Criterion 4 is the one that mattered,
and its target wasn't the problem. Its checks were: they measured format, and
format is the part the model gets right. I revised criterion 4 (above and in
`criteria.md`). If I tightened another, it would be criterion 1, to 5 of 5.

*Checking the verdict.* I gave criterion 4, its five tries, try 1's cards and
my original MET verdict to a fresh Claude session and asked it to argue the
opposite. Its case was that the criterion promises "usable", and three of try
1's five cards ("Finally parting with…", "Find it live on my Depop") can't be
posted by a shopper, so try 1 is 2/5. That is the revision. It also pointed out
that the sentence count is gameable: a 50-word run-on counts as one sentence,
and a final line ending in an emoji isn't counted at all. That's true. I've
noted it, but I didn't revise the criterion a second time, because no card in
this run was unreadable for that reason.

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
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: lst_002 · Y2K Baby Tee — Butterfly Print ($18, depop)
[4] suggest_outfit
      in:  lst_002 · Y2K Baby Tee — Butterfly Print ($18, depop)
      out: Grab that butterfly baby tee, it is a great find for eighteen dollars.   Outfit one leans into that nostalgic …
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  lst_002 · Y2K Baby Tee — Butterfly Print ($18, depop)
      out: Scored this Y2K baby tee with the cutest butterfly print for just $18 on Depop, and I've been obsessed with st…
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: stopping before suggest_outfit
```

The empty trace is 3 steps and the happy trace is 5: it stops at the branch.
The same `lst_002` id appears in `select_item` and in the inputs of both
`suggest_outfit` and `create_fit_card`, which is what criterion 3 checks.

**Failures triggered on purpose**

1. *Empty search*: `python app.py ask 'gold sequin tuxedo jacket size XXS under $3'`
   ```
   Nothing in the listings matched description 'gold sequin tuxedo jacket', size XXS, under $3.
   Things to change: try fewer words — 'jacket' alone finds more than 'gold sequin tuxedo jacket'; drop the size, or try a neighbouring one; raise the price ceiling above $3.
   ```
   It stopped at the branch with 0 model calls. The first version used a fixed
   example ("'jacket' finds more than 'cropped corduroy jacket'") that had
   nothing to do with the query. The "fewer words" example is now built from
   the user's own description.

2. *Empty wardrobe*: `python app.py ask 'denim jacket under $50' --empty-wardrobe`.
   There was no crash and no empty string. `suggest_outfit` returned two
   general outfits, and the fit card was written from them. The first version
   never said there was no wardrobe, so the outfits read as if the app had
   invented clothes the user owns. The output now opens with a fixed line,
   added in code rather than left to the model:
   ```
   You haven't saved any wardrobe items, so these are general ideas, not pieces you own. Add your clothes to your wardrobe to get outfits built from what you already have.
   ```

3. *Model unavailable*: one character of `GEMINI_API_KEY` in `.env` changed,
   then a query not asked before: `python app.py ask 'olive canvas shacket size M'`
   ```
   The search worked: it found 1 listing(s), best match Shacket — Olive Canvas ($33 on poshmark). But the AI model couldn't be reached, so no outfit or caption was written.
   Why: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
   Once that's fixed, run the same query again.
   ```
   It returned at once, with no hang and no stack trace. The first version of
   this message said "Check GEMINI_API_KEY" twice and gave key advice even when
   the cause could be a network error. Now the service's own reason comes
   through under "Why", and the message keeps what the search found, so the run
   isn't a total loss.

4. *Search server unavailable* (MCP; not one of the required three, but new
   this unit): with the client pointed at a server path that doesn't exist,
   the run stopped with "The search service didn't respond, so nothing was
   searched and no outfit was written… Try the same query again; if it fails
   twice, run `python mcp_client.py`…" and not a raw `MCPError` traceback.
   This handler was added in this milestone.

**Checking the messages.** I gave the three messages to a fresh Claude session
that had never seen the code, with the assignment's prompt ("tell me what I
would try next… don't rewrite them"). The empty search: it would drop the size,
raise the price, then shorten to "jacket". It found the fixed example confusing.
The empty wardrobe: it thought the app had "made those pieces up" and couldn't
tell that saving a wardrobe would help. The model unavailable: the fix is clear
if you run the app yourself, but there's nothing to do if someone else hosts
it. That's acceptable for a command-line tool you run yourself, so it stayed.
The first two led to the fixes above.

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

**What I changed:** one prompt, in `tools.py::create_fit_card`. I added a
paragraph saying who is posting: *"The person posting is the BUYER. They just
bought this secondhand and are showing off their find and how they're styling
it. They are not selling it, have not listed it, and are keeping it — never
write it as a listing or invite anyone to buy it."* Two labels changed to
match: `Price:` became `Price they paid:`, and `Platform:` became `Where they
found it:`. The instruction to mention the platform now says "where they found
it". Nothing else changed: same tools, loop, scenarios, temperature and scorer.

**Which failure it was meant to fix:** criterion 4 (revised), MISSED 0/5. In the
before run, 26 of 65 fit cards were written as the seller ("Finally parting
with this 90s leather bomber…", "It's up on my Poshmark for $45 if you want to
make it yours"). The diagnosis put this in the model's output, caused by a
prompt that never said the poster bought the item, so the fix is in the prompt.

### Run Log — Before (for comparison)

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item is the item passed on (by id) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2-4 sentences, $price, platform | 4 of 5 cards, no repeat opening | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4R. Fit card (revised): + buyer's voice, not seller's | 4 of 5 cards, no repeat opening | FAIL | FAIL | FAIL | FAIL | FAIL | **MISSED (0/5)** |
| 5. Search respects the price ceiling | 5 of 5 queries | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

### Run Log — After

`python score_eval.py --label after` runs `run_eval.py::main` with the label
`after` (14 scenarios, 5 tries, cache off, 131 real model calls), then scores
those sessions with the same rules as before. Files:
`results/run_2026-10-09_2302_after.md` and `results/score_after.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item is the item passed on (by id) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2-4 sentences, $price, platform | 4 of 5 cards, no repeat opening | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4R. Fit card (revised): + buyer's voice, not seller's | 4 of 5 cards, no repeat opening | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Search respects the price ceiling | 5 of 5 queries | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** Yes. Revised criterion 4 went from
**MISSED (0/5) to MET (5/5)**, and seller-voice cards went from **26 of 65 to 0
of 65** across every scenario that writes a card, not only the five criterion 4
scores. To check the scorer wasn't just missing new wording, I also searched
all 65 after-cards for broader sale words ("sell", "sale", "listing",
"available", "link", "DM", "yours"…) and found none. The track jacket, the
worst item before (5/5 seller), now reads like a buyer:

```
Scored this amazing 90s track jacket on Poshmark for just $45 and I am so obsessed with it. I’ve been styling it two ways lately: layered casually over a white ribbed tank and baggy denim for a sporty streetwear vibe, or dressed up with wide-leg khakis for that high-low contrast. It's such an easy piece to throw on and instantly pulls the whole look together.
```

and the leather bomber, which was "Finally parting with this…" twice before:

```
Scored this vintage 90s leather bomber on Depop for just $75 and I'm obsessed. I'm leaning into the grunge aesthetic today by pairing it with a simple white tank, baggy dark wash jeans, and chunky combat boots. For a more modern streetwear contrast, I've been throwing it on over a cropped zip hoodie with fresh white sneakers.
```

Nothing else got worse. Criteria 1, 2, 3 and 5 stayed at 5/5, and average card
length is the same (285 → 293 characters).

**One honest cost.** Criterion 4's per-try note shows two cards failing as
"1 sentence" (silk slip dress in try 2, track jacket in try 4). Both are really
two sentences: the second ends in an emoji with no period, so the counter
doesn't see it. That's the counting weakness noted in the diagnosis, not
shorter captions. Cards counted as under 2 sentences went from 4 to 7 of 65,
which is within run-to-run variation, since none of the before ones happened to
land in a criterion-4 scenario. It didn't change a verdict, because each try
still had 4+ of 5 passing. But with one more such card in a try, criterion 4
would have "missed" because of the counter, not the caption.

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
