"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # Criterion 3 — state. Any matching query works; what's checked is that
        # the id in session["selected_item"] is search_results[0]'s id and is
        # the id the trace shows going into suggest_outfit and create_fit_card.
        "name": "state carries the selected item",
        "query": "chunky knit cardigan",
        "wardrobe": "example",
        "criterion": 3,
    },

    # Criterion 4 — the fit card, across 5 queries that select 5 DIFFERENT
    # listings (lst_004, lst_013, lst_019, lst_005, lst_022; three platforms).
    # One "try" of criterion 4 is one pass over all five: 4+ of the 5 cards
    # must be 2-4 sentences with "$price" and the platform, and no two may
    # share an opening sentence.
    {"name": "fit card: track jacket", "query": "90s track jacket in size M",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card: silk slip dress", "query": "silk slip dress in midi length under $40",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card: platform sneakers", "query": "platform sneakers size 8",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card: corduroy pants", "query": "corduroy wide-leg pants",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card: leather bomber", "query": "leather bomber jacket",
     "wardrobe": "example", "criterion": 4},

    # Criterion 5 — the price ceiling, across 5 "under $N" queries. Two sit
    # exactly on the ceiling (cardigan $35, tee $20) to test "inclusive".
    # One "try" of criterion 5 is one pass over all five: parsed max_price == N
    # and no result over N, for every one of them.
    {"name": "price ceiling: denim jacket $50", "query": "denim jacket under $50",
     "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling: graphic tee $20", "query": "graphic tee under $20",
     "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling: cardigan $35", "query": "cardigan under $35",
     "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling: boots $45", "query": "boots under $45",
     "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling: flannel $25", "query": "flannel shirt under $25",
     "wardrobe": "example", "criterion": 5},
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
