# Как залить мега-шаблон в `overbaffe1/gitEdit` с авто-распаковкой

Рядом лежат два файла:
* **`unpack.yml`** — GitHub Action, который автоматически распаковывает любые загруженные `.zip`-архивы в корень репозитория и удаляет сам архив.
* **`gitEdit-mega-template.zip`** — полный архив витрины `gitEdit` (`README.md`, анимированные SVG-баннеры `assets/` под тёмную и светлую темы, шаблоны проекта и профиля `templates/` + воркфлоу змейки коммитов).

## Способ 1. Через авто-распаковку на GitHub Actions (в 2 шага в браузере)

Так как `overbaffe1/gitEdit` изначально пустой, GitHub должен сначала узнать о самом экшене распаковки:

1. Открой **[github.com/overbaffe1/gitEdit](https://github.com/overbaffe1/gitEdit)** и нажми синюю ссылку **`creating a new file`**.
2. В поле имени файла введи точно:
   ```text
   .github/workflows/unpack.yml
   ```
   Вставь содержимое файла `unpack.yml` и нажми зелёную кнопку **Commit changes...**.
3. Теперь на главной репо нажми **`Add file` → `Upload files`**, перетащи туда **`gitEdit-mega-template.zip`** и нажми **Commit changes**.
4. Подожди ~15–20 секунд и обнови страницу: GitHub Actions сам распакует все папки и файлы, удалит `.zip` и зажжёт зелёный бейдж **`Auto Unpack | passing`** в шапке `README.md`! В будущем в этот репо можно кидать любые другие `.zip` — он будет распаковывать их автоматически.

## Способ 2. Без Actions (просто распаковать на ПК)

Распакуй `gitEdit-mega-template.zip` у себя на компьютере и перетащи разархивированные файлы (`README.md`, `assets`, `templates`) в окно **`uploading an existing file`** на странице `github.com/overbaffe1/gitEdit`.
