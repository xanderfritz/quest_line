# api design

## auth

token based. the user POSTs username + password to /api/token/ and gets back a token. every other api call sends `Authorization: Token <key>`.

the project uses DRF's built in `rest_framework.authtoken`. no JWT, no third party lib.

the default permission in settings is `IsAuthenticated`. endpoints add role-based checks on top.

## endpoints

| method | url | who | purpose |
| ------ | --- | --- | ------- |
| POST | /api/token/ | anyone | exchange username+password for a token |
| GET | /api/articles/ | any authed | list all approved articles |
| POST | /api/articles/ | journalist | create an article (author auto set to the caller) |
| GET | /api/articles/\<id\>/ | any authed | retrieve one article |
| PUT | /api/articles/\<id\>/ | editor or author | update |
| DELETE | /api/articles/\<id\>/ | editor or author | delete |
| GET | /api/articles/subscribed/ | any authed | approved articles from the readers subscribed publishers and journalists only |
| POST | /api/approved/ | internal | the signal POSTs here on approval as a log endpoint |

## serializers

- `UserSerializer` - id, username, email, role
- `PublisherSerializer` - id, name, description
- `ArticleSerializer` - id, title, content, author, publisher, approved, created_at (approved + created_at + author are read only, author is set in the view)
- `NewsletterSerializer` - id, title, description, author, articles, created_at

## status codes

- 200 OK for successful GET
- 201 Created for POST
- 204 No Content for DELETE
- 400 Bad Request for bad payload / failed token exchange
- 401 Unauthorized when no token / invalid token
- 403 Forbidden when role mismatch (e.g. reader tries to POST)
- 404 Not Found

## permissions logic

custom `ArticlePermission` class:

- request must be authenticated
- GET - any authed user
- POST - journalists only
- PUT / DELETE - editors always, journalists only on their own articles

## testing

- 21 automated unit tests in `chronicle/tests.py`
- postman can be used for manual exploration but is not the submission requirement
- signal side effects (email + requests.post) are mocked via `unittest.mock.patch`
