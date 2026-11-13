# quest line

a django news application with a dark fantasy twist. journalists write articles, editors approve them, readers subscribe to their favourite publishers and journalists and get emailed when new approved articles drop. ships with a full REST API (token auth) and a dark souls style ui.

built as the hyperiondev capstone project (M06T08).

## features

- custom User model (reader, editor, journalist roles) with group based permissions
- publishers with editors and journalists
- articles with an approval workflow
- newsletters that bundle articles
- reader subscriptions to publishers and journalists
- editor approves an article -> post_save signal emails subscribers + POSTs to /api/approved/
- rest api with DRF token auth
- dark fantasy ui (Cinzel + EB Garamond fonts, parchment / gold on near black)
- 21 passing automated unit tests covering roles, api, subscriptions, signals, mocks

## setup

### 1. mariadb

```sh
sudo mariadb <<EOF
CREATE DATABASE quest_line CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'quest_line'@'localhost' IDENTIFIED BY 'quest_line';
GRANT ALL PRIVILEGES ON quest_line.* TO 'quest_line'@'localhost';
GRANT ALL PRIVILEGES ON \`test_quest_line\`.* TO 'quest_line'@'localhost';
FLUSH PRIVILEGES;
EOF
```

the second grant lets the django test runner create its test database.

### 2. venv + deps

```sh
python3 -m venv venv
source venv/bin/activate
pip install django djangorestframework requests mysqlclient
```

if mysqlclient fails to build, use the pure python driver (the project falls back automatically):

```sh
pip install pymysql
```

### 3. migrate and run

```sh
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

open http://127.0.0.1:8000/

## roles

- **reader** - view articles and newsletters, subscribe to publishers and journalists
- **journalist** - create, view, edit, delete own articles and newsletters
- **editor** - view, approve, edit, delete any article / newsletter

groups and permissions are auto created on migrate.

## rest api

all endpoints require a token in the `Authorization: Token <key>` header, except `/api/approved/` (internal).

| method | url | who | what |
| ------ | --- | --- | ---- |
| POST | /api/token/ | anyone | swap username + password for a token |
| GET | /api/articles/ | any authed user | list all approved articles |
| POST | /api/articles/ | journalist | create an article |
| GET | /api/articles/<id>/ | any authed user | one article |
| PUT | /api/articles/<id>/ | editor or author | update |
| DELETE | /api/articles/<id>/ | editor or author | delete |
| GET | /api/articles/subscribed/ | any authed user | approved articles from the readers subs only |
| POST | /api/approved/ | internal | signal logs approved articles here |

### quick api example

```sh
# get a token
curl -X POST http://127.0.0.1:8000/api/token/ \
  -d "username=scribe1&password=yourpass"

# list approved articles with it
curl http://127.0.0.1:8000/api/articles/ \
  -H "Authorization: Token <the-token>"
```

## approval workflow (signals)

1. a journalist creates an article - `approved=False`
2. an editor opens `/editor/queue/` and clicks approve
3. `article.approved` flips to `True`, the model saves
4. a `post_save` signal fires:
   - gathers every reader subscribed to the author journalist or the publisher
   - sends an email to each (console backend in dev - prints to the terminal)
   - POSTs the article to `/api/approved/` via `requests` as an audit log

both actions are mocked in the test suite.

## tests

```sh
python manage.py test chronicle
```

21 tests cover:

- auth per role
- reader sees subscribed content only
- journalist can create
- editor can approve + delete
- newsletters behave correctly
- signal fires on approval (mocked email + mocked requests.post)
- success + failure cases

## layout

- `quest_line/` project settings and root urls
- `chronicle/` the app
  - `models.py` custom User, Publisher, Article, Newsletter
  - `views.py` regular html views
  - `api_views.py` DRF api endpoints
  - `serializers.py` DRF serializers
  - `permissions.py` role based api permissions
  - `signals.py` post_save approval signal
  - `apps.py` auto creates groups with perms on migrate, registers signals
  - `forms.py` register + article + newsletter forms
  - `urls.py` all routes
  - `tests.py` automated unit tests
  - `templates/` html templates
  - `static/` css
- `Planning/` design docs (requirements, api design, sequence diagram, ui plan)
