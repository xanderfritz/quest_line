# ui plan

a simple dark fantasy theme. kept basic on purpose (student project), the atmosphere comes from the colour palette rather than fancy fonts or effects.

## colours

- background: #1a1510 (dark brown black)
- header / cards: #0d0b08 / #241c15 (slightly darker + slightly lighter panel)
- gold text accents: #c9a961
- muted text: #8a7444
- body text: #d0c4a3 (parchment)
- danger red: #c94a3a
- borders: #3a2e22

## typography

- system serif (`Georgia, serif`) for everything - no google fonts, nothing to download
- normal case (lowercase in nav labels is a style choice)

## layout

- plain header bar with brand + nav links
- content area is max 1000px wide, centered
- cards for articles and newsletters in a vertical list
- forms use default django `{{ form.as_p }}` rendering with a bit of css polish
- footer with one line

## pages

- `/` home - hero line + latest approved articles
- `/article/<id>/` single article (shows approved or pending tag)
- `/newsletters/` list, `/newsletters/<id>/` detail
- `/register/`, `/login/`
- `/articles/new/`, `/articles/mine/` (journalists)
- `/newsletters/new/` (journalists)
- `/editor/queue/` (editors) with approve + delete buttons
- `/subscriptions/` (readers) with checkboxes for publishers + journalists

## naming

- buttons use plain words (submit, save, approve, delete, login) rather than in-world jargon
- the theme stays visible through the dark palette and gold accents, not through flavour text
