# requirements

## what the app is

a news application. independent journalists and in-house journalists at publishers write articles. editors review and approve them. readers subscribe to publishers or journalists and get emailed when content they follow is published. there is also a REST API so a third party client can pull articles.

the ui uses a dark fantasy theme (quest line, dark souls inspired).

## functional requirements

### readers
- register as a reader
- browse all approved articles and newsletters
- read a single article / newsletter
- pick subscriptions (one or more publishers, one or more journalists)
- get an email when an article by a subscribed author or publisher is approved
- use the REST API to pull approved articles (incl. only their subscriptions)

### journalists
- register as a journalist
- write, view, update, delete their own articles
- pick a publisher or stay independent
- create newsletters (title + description + choose articles)
- use the REST API to create and manage their own articles

### editors
- register as an editor
- open the review bench to see all unapproved articles
- approve or delete articles
- edit / delete newsletters

### admin (superuser)
- manage every model via django admin
- create publishers
- assign editors / journalists to publishers
- change roles / groups

### system wide
- custom user model with a role field
- three auto created groups with permissions (Reader, Editor, Journalist)
- post_save signal on Article - when approved flips to True:
  - email every subscribed reader
  - POST the article to /api/approved/ as a log
- REST API with DRF token based auth

## non functional requirements

- normalised database on mariadb
- PEP 8 code
- modular code (views, api_views, serializers, permissions, signals, forms split)
- defensive coding - try/except on third party calls, 404s via get_object_or_404, permission classes
- csrf protection on forms, token auth on api
- passwords hashed by djangos default PBKDF2
- 21 automated unit tests (python, not just postman)
- works on any machine with python, mariadb, and the listed pip deps
- dark fantasy ui that stands out from earlier tasks
