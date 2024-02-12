
## Urls out of the box

- `/api/healthcheck/` -> Health checks
- `/api/` -> API endpoints. Login required
- `/api/docs/` -> API documentation. Login required
- `/api/openapi.json` -> Open API schema. Login required

## Development

NOTE: The following command makes the assumption that you are using `docker compose` version `>2`. if you are using a older version, please replace `docker compose` with `docker-compose`

### Running local environment

```bash
docker compose -f local.yml up
```

### Creating translations with gettext

Install gettext

```bash
apt install gettext
```

generate translations files and remove base.po~ files

```bash
/usr/bin/pygettext3 -d base -o locales/base.pot ./src ./config
msgmerge locales/en/LC_MESSAGES/base.po locales/base.pot -U
msgmerge locales/es/LC_MESSAGES/base.po locales/base.pot -U
msgfmt -o locales/es/LC_MESSAGES/base.mo locales/es/LC_MESSAGES/base
msgfmt -o locales/en/LC_MESSAGES/base.mo locales/en/LC_MESSAGES/base
```

### Creating and running alembic versions

```bash
docker compose -f local.yml run --rm fastapi alembic revision --autogenerate -m "Brief description"
docker compose -f local.yml run --rm fastapi alembic upgrade head
```

For advanced options -> <https://alembic.sqlalchemy.org/en/latest/tutorial.html#partial-revision-identifiers>

### Running the tests

```bash
docker compose -f local.yml run --rm fastapi python -m pytest
```

### Showing tests coverage

First run test with coverage to collect information

```bash
docker compose -f local.yml run --rm fastapi coverage run -m pytest
```

To see a summary

```bash
docker compose -f local.yml run --rm fastapi coverage report
```

or if you want to generete a complete html report you can type:

```bash
docker compose -f local.yml run --rm fastapi coverage html
```

### Getting a shell inside Docker container

```
docker compose -f local.yml run --rm fastapi python -i ./main.py
```

### Install pre-commit locally

```bash
python3 -m venv venv/test
source ./venv/test/bin/activate
pip install -r requirements/local.txt
pre-commit install
```

# Commands
You can use `cli.py` to run specific actions. Type the following command to get more information
```bash
docker compose -f local.yml run --rm fastapi python cli.py --help
```
