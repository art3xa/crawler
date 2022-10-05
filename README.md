# Crawler

Версия 0.2

Авторы: Артём Романов (artem.romanov.03@bk.ru), Евгений Сергеев ()

Ревью выполнили:

## Описание

Веб-краулер без индексирования с robots.txt

## Требования

* Python версии не ниже 3.6 (используется 3.10.2)
* aiohttp версии 3.8 или выше (используется 3.8.1)
* yarl версии 1.8 или выше (используется 1.8.1)
* asyncio версии 3.4 или выше (используется 3.4.3)
* lxml версии 4.9 или выше (используется 4.9.1)

## Состав

* Запуск: `main.py`
* Логика: `crawler.py`
* Модули: `src/`

## Консольная версия

Справка по запуску: `python src/main.py --help`
Пример запуска: `python src/main.py {link}`

## Подробности реализации

## Реализовано

- Поддержка robots.txt
- Асинхронность

### Фиксы


