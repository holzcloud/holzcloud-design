# holzcloud-design

The design template behind everything holzcloud runs: the site at
[holzcloud.ch](https://holzcloud.ch), the holzkube management UI, the
holzcloud-cms administration, the Authentik login and the Homepage dashboard.

Plain CSS custom properties and plain CSS components. No build step, no
package manager, no framework — because two of the four consumers cannot have
one, and a design system that only the newest project can use is not a design
system.

Open [`docs/index.html`](docs/index.html) in a browser. That page loads the
same files that ship, so if something looks wrong there it is wrong in the
system.

| Path | What |
|---|---|
| `css/tokens.css` | Every value, decided once. 80 of them. |
| `css/base.css` | The ground, the type, the focus ring, the two accessibility settings. |
| `css/components.css` | Panes, buttons, chips, status, alerts, forms, tables, text roles. |
| `css/holzcloud.css` | The three above in one `@import`, for convenience. |
| `css/motif.css` | The cube texture and the drawing vocabulary. |
| `css/shadcn-bridge.css` | Points shadcn/Tailwind's variable names at the tokens. |
| `logo/` | The holzkube mark, in the sizes it actually needs. |
| `tokens.json` | The same values, machine-readable. Generated from `tokens.css`. |
| `docs/index.html` | The specimen. Every token and every component on one page. |
| `tools/` | The two scripts CI runs. |

## Using it

### Static HTML — holzcloud.ch, Authentik, Homepage

```html
<link rel="stylesheet" href="/css/tokens.css">
<link rel="stylesheet" href="/css/base.css">
<link rel="stylesheet" href="/css/components.css">
```

`css/holzcloud.css` pulls in all three with `@import`, which costs one extra
round trip because an `@import` is only discovered after the importing file has
been fetched and parsed. Convenient for a prototype; link the three directly
where it matters.

The typefaces are not bundled. Load Manrope and JetBrains Mono however the
consuming project already loads fonts, or change `--hc-font-sans` and
`--hc-font-mono` to something local.

### Go templates — holzcloud-cms

Copy the three files into `cmd/holzcloud/assets/` and let `embed.FS` pick them
up. No new dependency and no build step: it stays plain CSS with `@layer`,
which the project's stack mandate allows by name.

### React with Tailwind and shadcn — holzkube

```css
@import "tailwindcss";
@import "shadcn/tailwind.css";
@import "../../design/css/tokens.css";
@import "../../design/css/shadcn-bridge.css";
```

The bridge maps `--primary`, `--card`, `--radius`, `--sidebar` and the rest onto
the brand tokens. No shadcn component is touched, and the generated
`@theme inline` block keeps working — it reads the same variable names and
knows nothing about the change.

Two things it changes on purpose, both spelled out in the file:

- It maps `:root` **and** `.dark` to the same values. holzcloud has one theme
  and it is dark. A light mode would be a second brand.
- It sets `--font-sans` to Manrope, which means dropping Geist. Two typefaces
  across four surfaces is the most visible way for them to stop looking like
  one product.

### The motif — `css/motif.css`

The isometric cube is in the name holzkube, in the logo, and in the texture
behind every page. `motif.css` holds both: `.hc-cubes` for the texture, and the
`.hc-iso` vocabulary for building drawings out of the same geometry.

It is deliberately **not** in `holzcloud.css`. An administration screen does not
show the motif and should not load it.

It is also not optional wherever `.hc-pane` sits over the gradient. A
`backdrop-filter` needs edges to refract; over a smooth gradient a frosted pane
reads as brown paint. Leave the texture out and the glass stops being glass.

`.hc-cubes` goes first in the `<body>`. Everything after it lifts itself above
the texture with a sibling rule — including one line that hands `.hc-bar` its
`position: sticky` back, because `hc.motif` layers after `hc.components` and
would otherwise take it away. That is the same sticky bug the bar's own comment
warns about, arriving through the back door.

```html
<body>
  <div class="hc-cubes" aria-hidden="true"></div>
  <header class="hc-bar">…</header>
```

The texture is a **mask** over a colour fill rather than a coloured image. A
hex inside a `data:` URI would be the one value in the system that could not
follow `--hc-brass`; as a mask, it does.

### The logo

`logo/holzkube-mark.svg` is the name in one figure: the isometric cube is the
*Kube*, the growth rings on the cut face are the *Holz*. A square-sawn beam
shows exactly that, and the cube is the same geometry already behind the page.

| File | For |
|---|---|
| `holzkube-mark.svg` | 24px and up. Draws in `currentColor`. |
| `holzkube-mark-small.svg` | Below that. Two rings instead of four, heavier stroke. |
| `holzkube-lockup.svg` | Mark and wordmark. |
| `holzkube-favicon.svg` | Fixed colour — a browser tab gives the file no text colour, and `currentColor` would be black there. |

Two rings and not four below 24px because four converge into a smudge, and what
survives is a cube with a dirty rim.

In 2:1 isometry a circle on the top face becomes an ellipse with a horizontal
major axis and `rx:ry = 2:1`, so the rings are plain `<ellipse>` elements with
no transform. With a transform the stroke width scales too, and
`vector-effect="non-scaling-stroke"` did not hold up in testing — the rings
rendered 26× thick and filled the face solid.

`logo/alternatives/` keeps the two that were not chosen, so the decision stays
readable: three laminated planks is clean but it is a parcel box, and there are
enough of those; a cube inside a box says cluster but says nothing about wood,
which loses one of the two syllables in the name.

### Anything else

`tokens.json` holds the same values grouped by role, for a tool that cannot
parse CSS.

## The rules this repository enforces

`tools/check.py` and `tools/tokens.py --check` run in CI, and both fail the
build rather than warning.

- **Every `var(--hc-…)` resolves.** A typo in a custom property name is silent
  in CSS — the declaration is simply dropped — so nothing else would ever
  report it.
- **No literal colour in `components.css`.** A hex or `rgb()` in a component is
  exactly how a design system stops being one. Add the value to `tokens.css`
  and reference it.
- **Braces balance** in every stylesheet.
- **`tokens.json` matches `tokens.css`.** It is generated; a stale copy is
  worse than none, because something will trust it.
- **The specimen links files that exist.**

## Decisions worth not re-litigating

**One theme, and it is dark.** Every holzcloud surface is dark. Nothing below
is named "dark" for exactly this reason: should a light theme ever be needed,
it is one extra block redefining the same names.

**One accent.** Brass points at one thing per screen. That is also why the
primary button is near-white and not brass — a page of brass buttons has no
accent left.

**`--hc-ink-3` is a floor, not a suggestion.** It carries the smallest type in
the system, and at 52% alpha it lands between 4.5:1 and 4.9:1 against the range
this ground actually produces. It was 42% once and failed AA.

**`--hc-warn` is a near neighbour of `--hc-brass`.** Not an oversight to be
fixed: the brand accent *is* amber. Never let colour alone carry the difference
between "attention" and "warning" — give the warning a word or an icon too.

**Destructive is outlined, not filled.** A red block is the easiest thing on a
screen to hit by accident.

**Glass needs its two guards.** `@supports not (backdrop-filter: …)` and
`prefers-reduced-transparency` both switch the panes to a real colour and drop
the gradient. Opaque panes alone would leave the gradient as the only thing
still moving behind text, which is the thing the setting is about.

**Sticky goes on the element itself.** A sticky wrapper exactly as tall as its
contents travels zero pixels and silently scrolls away. `.hc-bar` is the fix,
and the comment above it is there so nobody rediscovers the bug.

## Changing a value

```sh
$EDITOR css/tokens.css
python3 tools/tokens.py      # regenerate tokens.json
python3 tools/check.py       # the rules above
open docs/index.html         # look at it
```

Adding a component means a class in `components.css`, a block in
`docs/index.html` showing it, and a sentence saying what it is *for* — a
component nobody can tell apart from the one above it is how the system grows
without getting better.
