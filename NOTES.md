# Data Notes — Milestone 1

What I found reading `data/listings.json` and `data/wardrobe_schema.json`
before writing any tools.

## Listing fields (what `search_listings` can filter on)

40 listings. Every listing has these 11 fields:

| Field         | Type        | What's in it |
|---------------|-------------|--------------|
| `id`          | str         | `lst_001` … `lst_040` |
| `title`       | str         | e.g. "Vintage Levi's 501 Jeans — Medium Wash" |
| `description` | str         | free text; condition details, fit notes |
| `category`    | str         | tops (15), bottoms (10), outerwear (8), shoes (4), accessories (3) |
| `style_tags`  | list[str]   | `vintage`, `graphic tee`, `y2k`, `grunge`, `streetwear`, … |
| `size`        | str         | **not standardized**, see below |
| `condition`   | str         | good (19), excellent (17), fair (4) |
| `price`       | float       | $12.00 – $75.00 |
| `colors`      | list[str]   | e.g. `["red", "black"]` |
| `brand`       | str or null | **null in 32 of 40 listings** |
| `platform`    | str         | depop (18), thredUp (11), poshmark (11) |

### Things that will bite when filtering

- **Size is free text.** Values include `M`, `S/M`, `M/L`, `L/XL`,
  `XL (oversized)`, `W30 L30`, `W28`, `US 8`, `US 8.5`, `One Size`,
  `One Size (adjustable)`. Exact match on `"M"` misses `S/M` and `M/L`;
  "size 8" has to match `US 8`.
- **Brand is usually null.** Anything reading `brand` must handle `None`.
- **Keywords live in several places.** "graphic tee" appears in
  `style_tags` and `title`; "90s" may be only in tags or title. Searching
  one field misses matches — search title + description + style_tags.

## Wardrobe shape (what `suggest_outfit` receives)

```json
{
  "items": [
    {
      "id": "w_001",
      "name": "Baggy straight-leg jeans, dark wash",
      "category": "bottoms",
      "colors": ["dark blue", "indigo"],
      "style_tags": ["denim", "streetwear", "baggy"],
      "notes": "High-waisted, sits above the hip"
    }
  ]
}
```

- `category` is one of: tops, bottoms, outerwear, shoes, accessories.
- `notes` is optional and can be `null`.
- The example wardrobe has 10 items.

**An empty wardrobe is `{"items": []}`.** `suggest_outfit` has to handle
this case and not crash or invent pieces the user doesn't own.

## Starter run

```
$ python app.py ask 'vintage graphic tee under $30'

  The planning loop isn't built yet — see the TODO in agent.py.

0 model calls this session
```

This is the expected starting position: the starter runs, and nothing is built yet.
