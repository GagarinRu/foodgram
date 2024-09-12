[![Main Foodgram workflow](https://github.com/GagarinRu/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/GagarinRu/foodgram/actions/workflows/main.yml/)
#  Проект Foodgram

Сайт проекта: https://gagarinfoodgram.zapto.org/

## Описание

Данный проект проект «Фудграм» предоставляет возможность пользователям публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.

## Реализованный стек со следующими параметрами:
- Django==3.2.3
- djangorestframework==3.12.4
- djoser==2.1.0
- gunicorn==20.1.0
- Pillow==9.0.0
- django-filter==23.1
- python-dotenv==1.0.1
- psycopg2-binary==2.9.3
- short_url==1.2.2

### Как развернуть проект:

*1.Склонировать проект с репозитория на GitHub:*

*2.Создать в Docker образы foodgram_backend, foodgram_frontend, foodgram_gateway и отправить на Docker Hub:*

docker build -t username/foodgram_backend .

cd ../backend

docker build -t username/foodgram_frontend .

cd ../gateway

docker build -t username/foodgram_gateway .

docker push username/foodgram_backend

docker push username/foodgram_frontend

docker push username/foodgram_gateway

*3.Зайти на сервер проекта и очистить диск сервера от лишних данных:*

*Удалить кеш npm: npm cache clean --force;*

*Удалить кеш APT: sudo apt clean.*

*Удалить старые системные логи: sudo journalctl --vacuum-time=1d*

*Полезно будет выполнить команду sudo docker system prune -af: она уберёт все лишние объекты, которые вы могли создать в докере за время выполнения заданий спринта, — неиспользуемые контейнеры, образы и сети.*

*Удалить Gunicorn-сервис (если установлен).*

*4.Настроить сервер Nginx для Foodgram так, что все запросы пойдут в Docker, на порт 8000.*

*5.В папке Foodgram создать файл .env  с переменными из проекта .*

*6.В настройках проекта на GitHub прописать необходимые для работы main.yml переменные.*

*7.Добавить, откоммитить и отправить проект на сервер GitHub.*

*8.После проверки в Action и сообщения в Телеграмм на сервере будет развернут проект Foodgram и подгружены Теги и Ингридиенты.*

### Как заполнить env

*Файл .env создается на сервере проекта и локально.*

*Внутри .env прописываются переменные, которые будут скрыты при публикации проекта.*

*В файле settings.py импортировать load_dotenv и прописать переменные в необходимых местах с помощью os.getenv().*


### Автор
Evgeny Kudryashov: https://github.com/GagarinRu