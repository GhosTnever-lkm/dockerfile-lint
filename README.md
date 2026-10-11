# dockerfile-lint

Офлайн-линтер Dockerfile: ловит небезопасные и неаккуратные решения до сборки образа — плавающие теги `:latest`, запуск от root, `curl … | sh`, секреты в `ENV`/`ARG`, лишние слои `apt-get`. Не запускает Docker и не ходит в сеть. Без зависимостей, Python 3.10+.

## Быстрый старт

```bash
python -m dockerfile_lint                       # ./Dockerfile
python -m dockerfile_lint services/*/Dockerfile --strict
python -m dockerfile_lint Dockerfile --json
python -m dockerfile_lint Dockerfile --ignore DL010   # пропустить правило
```

Пример вывода для [examples/bad.Dockerfile](examples/bad.Dockerfile):

```text
examples/bad.Dockerfile:1: [WARNING] DL001 base image 'ubuntu:latest' is unpinned or uses :latest
examples/bad.Dockerfile:2: [ERROR] DL008 ENV API_TOKEN looks like a secret stored in the image
examples/bad.Dockerfile:4: [ERROR] DL007 RUN pipes a remote download into a shell
```

## Правила

| Код | Уровень | Смысл |
| --- | --- | --- |
| `DL000` | error | в файле нет `FROM` |
| `DL001` | warning | базовый образ без тега или с `:latest` (digest `@sha256:` считается закреплённым) |
| `DL002` | warning | финальный этап не содержит `USER` — контейнер работает от root |
| `DL003` | warning | `ADD` для локальных файлов; нужен `COPY` (архивы и URL допустимы) |
| `DL004` | info | `apt-get install` без `--no-install-recommends` |
| `DL005` | warning | `apt-get install` без очистки `/var/lib/apt/lists` в том же слое |
| `DL006` | info | `pip install` без `--no-cache-dir` |
| `DL007` | error | `RUN` передаёт скачанный скрипт в shell (`curl … \| sh`) |
| `DL008` | error | `ENV`/`ARG` с секретоподобным именем и непустым значением |
| `DL009` | warning | несколько `CMD`/`ENTRYPOINT` в финальном этапе |
| `DL010` | info | нет `HEALTHCHECK` в финальном этапе |

Коды возврата: `0` — ок, `1` — есть ошибки (или предупреждения при `--strict`), `2` — файл не читается.

## Ограничения

- Это статическая эвристика, а не полный разбор shell. Сложные конструкции в `RUN` проверяются по шаблонам.
- Не проверяет существование образов и пакетов, не собирает образ.
- Строки продолжения (`\`) склеиваются; здесь не поддерживаются `heredoc` и `# syntax=` директивы.

## Разработка

```bash
python -m unittest discover -s tests -t .
```

## Лицензия

MIT — см. [LICENSE](LICENSE).

## История изменений и безопасность

См. [CHANGELOG.md](CHANGELOG.md) и [SECURITY.md](SECURITY.md).

## Использование в CI

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- name: dockerfile-lint
  run: python -m dockerfile_lint Dockerfile --strict
```
