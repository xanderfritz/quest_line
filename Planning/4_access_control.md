# access control

## roles

three auto created django groups, one per role, matched to the custom user `role` field:

| group | role string | perms |
| ----- | ----------- | ----- |
| Reader | reader | view article, view newsletter |
| Editor | editor | view / change / delete article + newsletter |
| Journalist | journalist | add / view / change / delete article + newsletter |

groups are created on `post_migrate` via a signal in `chronicle/apps.py` so a fresh clone sets itself up on `python manage.py migrate` with no extra steps.

on register, the view adds the user to the matching group based on the role they picked.

## per view protection

### html views
- `@login_required` on anything that writes data
- helper `_in_group(user, name)` checks the role for vendor / editor only pages
- `HttpResponseForbidden` returned on mismatch
- editor queue + approve + delete gated by `_in_group(user, 'Editor')`
- journalist create article / my articles / create newsletter gated by `_in_group(user, 'Journalist')`
- reader subscriptions gated by `_in_group(user, 'Reader')`

### api views
- `TokenAuthentication` + `IsAuthenticated` globally via DRF settings
- `ArticlePermission` class on the article endpoints adds:
  - POST - journalist only
  - PUT / DELETE - editor anyone, journalist only own article
  - object level check compares `obj.author_id` with `request.user.id`

### model level
- `limit_choices_to={'role': 'journalist'}` on `Article.author` and `Newsletter.author` so admin / forms cant pick a non journalist
- custom User `save()` clears reader-only subscription fields if the user is not a reader

## data safety

- passwords stored hashed via djangos default PBKDF2 hasher
- tokens are random keys issued by DRF, stored in db, not exposed outside the auth header
- csrf protection on all html forms (django middleware default)
- /api/approved/ is set to `AllowAny` because it is the receiver of our own signal. in production this would move to a shared secret or IP allow list

## failure handling

- `get_object_or_404` on all detail views
- try / except around `requests.post` in the signal so a failing internal endpoint cant block an article save
- `fail_silently=True` on the subscriber email so an unreachable email backend cant break the signal
- 401 / 403 / 404 / 400 returned from the api instead of 500 for expected error cases
