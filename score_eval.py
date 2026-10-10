#!/usr/bin/env python3
"""
Run the eval AND score it against criteria.md, from the same runs.

    python score_eval.py --label before

This calls run_eval.py's own main() — same scenarios, same five tries, cache
off, same results/run_*.md file — and records every session as it goes. Then
it applies the five criteria, exactly as written in criteria.md, to those
sessions and writes results/score_<label>.md: the run-log table plus the
reason for every FAIL.

run_eval.py leaves the PASS/FAIL judgement to you on purpose. This file IS
that judgement, written down as code so it's applied the same way every try
and anyone can check how a verdict was reached.

What counts as "one try" (column Try k):
  1, 2, 3  one run of that criterion's single scenario.
  4        the k-th run of all five fit-card scenarios: 4+ of the 5 cards pass
           AND no two of the 5 share an opening sentence.
  5        the k-th run of all five price-ceiling scenarios: all five pass.
"""

import re
import sys

import config
import run_eval
import scenarios as scenario_module

TARGETS = {1: 4, 2: 5, 3: 5, 4: 5, "4R": 5, 5: 5}  # tries out of 5 needed for MET
TARGET_TEXT = {
    1: "4 of 5",
    2: "5 of 5",
    3: "5 of 5",
    4: "4 of 5 cards, no repeat opening",
    5: "5 of 5 queries",
    "4R": "4 of 5 cards, no repeat opening",
}
TITLES = {
    1: "Matching query completes all three tools",
    2: "Impossible query stops before suggest_outfit",
    3: "Selected item is the item passed on (by id)",
    4: "Fit card: 2-4 sentences, $price, platform",
    5: "Search respects the price ceiling",
    "4R": "Fit card (revised): + buyer's voice, not seller's",
}


# ── one criterion, one session ───────────────────────────────────────────────

def check_1(rec):
    if rec["crashed"]:
        return False, f"crashed: {rec['crashed']}"
    s = rec["session"]
    if s["error"]:
        return False, f"stopped early: {s['error'].splitlines()[0]}"
    if not s["fit_card"] or s["fit_card"].startswith("Couldn't write a fit card"):
        return False, "no fit card"
    return True, ""


def check_2(rec):
    if rec["crashed"]:
        return False, f"crashed: {rec['crashed']}"
    s = rec["session"]
    if s["search_results"]:
        return False, f"search found {len(s['search_results'])} results"
    if s["outfit_suggestion"] is not None or re.search(r"\] suggest_outfit\b", rec["trace"]):
        return False, "suggest_outfit was called"
    if not s["error"] or "Things to change" not in s["error"]:
        return False, f"message doesn't name what to change: {s['error']!r}"
    return True, ""


def _trace_input(trace, step_name):
    m = re.search(rf"\] {re.escape(step_name)}\n\s+in:\s+(.*)", trace)
    return m.group(1) if m else ""


def check_3(rec):
    ok, why = check_1(rec)
    if not ok:
        return False, why
    s = rec["session"]
    sid, first = s["selected_item"]["id"], s["search_results"][0]["id"]
    if sid != first:
        return False, f"selected {sid} but search_results[0] is {first}"
    for step in ("suggest_outfit", "create_fit_card"):
        seen = _trace_input(rec["trace"], step)
        if not seen.startswith(sid + " "):
            return False, f"trace shows {seen!r} going into {step}, expected {sid}"
    return True, ""


def _sentences(text):
    return len(re.findall(r"[.!?]+(?=\s|$)", text.strip()))


def _opening(text):
    return re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0].lower()


def check_card(rec):
    ok, why = check_1(rec)
    if not ok:
        return False, why
    card = rec["session"]["fit_card"]
    item = rec["session"]["selected_item"]
    problems = []
    n = _sentences(card)
    if not 2 <= n <= 4:
        problems.append(f"{n} sentence(s)")
    price = f"{item['price']:g}"
    if not re.search(rf"\${price}(\.00?)?(?!\d)", card):
        problems.append(f"no ${price}")
    if item["platform"].lower() not in card.lower():
        problems.append(f"no '{item['platform']}'")
    return (not problems), ", ".join(problems)


# Criterion 4 as revised in unit 4 (see criteria.md): the card must also be in
# the BUYER's voice. A card fails if it says or implies the poster is selling
# the item — listed/up/live on their account, parting with it, or offering it
# to the reader. These patterns were checked by hand against all 40 cards from
# the before run (18 seller, 22 buyer) and agree on every one.
SELLER_PATTERNS = [
    r"\b(just )?(listed|dropped)\b",
    r"\b(up|live)( now)? on my\b",
    r"\bup now on\b",
    r"\bavailable now\b",
    r"\bparting with\b",
    r"\bmy (depop|poshmark|thredup)\b",
    r"\bbefore i change my mind\b",
    r"\bif (you|anyone( else)?) wants? to (snag|make it yours|grab)\b",
]


def seller_voice(card):
    """The first seller phrase found in the card, or None."""
    for pattern in SELLER_PATTERNS:
        m = re.search(pattern, card, re.I)
        if m:
            return m.group(0)
    return None


def score_card_set_revised(cards):
    """cards: list of (name, card, item). Revised criterion 4 for one try."""
    fails, openings = [], []
    for name, card, item in cards:
        problems = []
        n = _sentences(card)
        if not 2 <= n <= 4:
            problems.append(f"{n} sentence(s)")
        if not re.search(rf"\${item['price']:g}(\.00?)?(?!\d)", card):
            problems.append(f"no ${item['price']:g}")
        if item["platform"].lower() not in card.lower():
            problems.append(f"no '{item['platform']}'")
        phrase = seller_voice(card)
        if phrase:
            problems.append(f"seller voice: '{phrase}'")
        if problems:
            fails.append(f"{name}: {', '.join(problems)}")
        openings.append(_opening(card))
    passed = len(cards) - len(fails)
    repeats = len(openings) - len(set(openings))
    note = f"{passed}/{len(cards)} cards pass" + (" — " + "; ".join(fails) if fails else "")
    if repeats:
        note += f"; {repeats} repeated opening(s)"
    return passed >= 4 and repeats == 0, note


def check_price(rec, ceiling):
    if rec["crashed"]:
        return False, f"crashed: {rec['crashed']}"
    s = rec["session"]
    parsed = s["parsed"].get("max_price")
    if parsed != ceiling:
        return False, f"parsed max_price {parsed}, expected {ceiling:g}"
    over = [f"{r['id']} ${r['price']:g}" for r in s["search_results"] if r["price"] > ceiling]
    if over:
        return False, f"over ${ceiling:g}: {', '.join(over)}"
    return True, ""


# ── scoring ──────────────────────────────────────────────────────────────────

def score(runs, tries):
    """runs: list of (scenario, [record per try]). Returns {criterion: [(pass, note)]}."""
    by_crit = {}
    for scenario, recs in runs:
        by_crit.setdefault(scenario.get("criterion"), []).append((scenario, recs))

    table = {}
    for k in range(tries):
        for c, single in ((1, check_1), (2, check_2), (3, check_3)):
            for scenario, recs in by_crit.get(c, []):
                ok, why = single(recs[k])
                table.setdefault(c, []).append((ok, why))

        cards = [(sc, recs[k]) for sc, recs in by_crit.get(4, [])]
        if cards:
            results = [(sc, *check_card(r)) for sc, r in cards]
            passed = sum(ok for _, ok, _ in results)
            openings = [_opening(r["session"]["fit_card"]) for _, r in cards
                        if r["session"] and r["session"]["fit_card"]]
            repeats = len(openings) - len(set(openings))
            fails = [f"{sc['name'].split(': ')[1]}: {why}" for sc, ok, why in results if not ok]
            note = f"{passed}/{len(cards)} cards pass"
            if fails:
                note += " — " + "; ".join(fails)
            if repeats:
                note += f"; {repeats} repeated opening(s)"
            table.setdefault(4, []).append((passed >= 4 and repeats == 0, note))

        if cards and all(r["session"] and r["session"]["fit_card"] for _, r in cards):
            table.setdefault("4R", []).append(score_card_set_revised(
                [(sc["name"].split(": ")[1], r["session"]["fit_card"], r["session"]["selected_item"])
                 for sc, r in cards]))
        elif cards:
            table.setdefault("4R", []).append((False, "a fit-card run did not complete"))

        prices = [(sc, recs[k]) for sc, recs in by_crit.get(5, [])]
        if prices:
            results = []
            for sc, r in prices:
                ceiling = float(re.search(r"\$(\d+)", sc["query"]).group(1))
                results.append((sc, *check_price(r, ceiling)))
            fails = [f"{sc['query']}: {why}" for sc, ok, why in results if not ok]
            table.setdefault(5, []).append(
                (not fails, "; ".join(fails) or f"{len(results)}/{len(results)} queries pass")
            )
    return table


def write(table, tries, label):
    lines = [
        f"# Scored run log — {label}",
        "",
        "- Produced by: `score_eval.py::main` (runs `run_eval.py::main`, then scores)",
        f"- Tries: {tries}, caching off, temperature {config.TEMPERATURE}",
        "",
        "| Criterion | Target | " + " | ".join(f"Try {i}" for i in range(1, tries + 1)) + " | Verdict |",
        "|---|---|" + "|".join(["---"] * tries) + "|---|",
    ]
    for c in sorted((k for k in table if k), key=str):
        cells = table[c]
        n = sum(ok for ok, _ in cells)
        verdict = f"{'MET' if n >= TARGETS[c] else 'MISSED'} ({n}/{tries})"
        lines.append(
            f"| {c}. {TITLES[c]} | {TARGET_TEXT[c]} | "
            + " | ".join("PASS" if ok else "FAIL" for ok, _ in cells)
            + f" | {verdict} |"
        )
    lines += ["", "## Per-try notes", ""]
    for c in sorted((k for k in table if k), key=str):
        lines.append(f"**Criterion {c}**")
        lines.append("")
        for i, (ok, why) in enumerate(table[c], 1):
            lines.append(f"- Try {i}: {'PASS' if ok else 'FAIL'}" + (f" — {why}" if why else ""))
        lines.append("")
    path = config.RESULTS_DIR / f"score_{label}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(l for l in lines if l.startswith("|")))
    print(f"\nWrote {path.relative_to(config.ROOT)}")


def rescore(path):
    """
    Score revised criterion 4 from an existing run log, without re-running.
    Used to apply the unit 4 revision to the 'before' run.
    """
    text = open(path, encoding="utf-8").read()
    sections = {s.splitlines()[0]: s for s in re.split(r"\n### ", text)[1:]}
    items = {sc["name"]: sc for sc in scenario_module.SCENARIOS if sc.get("criterion") == 4}
    from utils.data_loader import load_listings
    by_title = {l["title"]: l for l in load_listings()}

    per_try = {}
    for name in items:
        sec = sections[name]
        tries = re.split(r"\*\*Try \d+\*\*", sec)[1:]
        for k, body in enumerate(tries):
            title = re.search(r"- selected_item: (.*?) \(\$", body).group(1)
            card = re.search(r"Fit card:\n\n```\n(.*?)\n```", body, re.S).group(1)
            per_try.setdefault(k, []).append((name.split(": ")[1], card, by_title[title]))
    table = {"4R": [score_card_set_revised(per_try[k]) for k in sorted(per_try)]}
    return table, len(per_try)


def main():
    if "--rescore" in sys.argv:
        path = sys.argv[sys.argv.index("--rescore") + 1]
        label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else "rescore"
        table, tries = rescore(path)
        write(table, tries, label)
        return

    label = "run"
    if "--label" in sys.argv:
        label = sys.argv[sys.argv.index("--label") + 1]
    tries = 5
    if "--tries" in sys.argv:
        tries = int(sys.argv[sys.argv.index("--tries") + 1])

    recorded = []
    original = run_eval.run_once

    def recording_run_once(scenario, use_trace=True):
        rec = original(scenario, use_trace)
        recorded.append((scenario, rec))
        return rec

    run_eval.run_once = recording_run_once
    run_eval.main()  # reads --label/--tries from sys.argv itself

    runs = []
    for scenario in scenario_module.SCENARIOS:
        recs = [r for sc, r in recorded if sc is scenario]
        runs.append((scenario, recs))
    print()
    write(score(runs, tries), tries, label)


if __name__ == "__main__":
    main()
