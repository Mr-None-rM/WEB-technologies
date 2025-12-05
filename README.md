# WEB-technologies

Django project within the field of web-technologies
Как запустить проект:
Создать .env файл как в примере(.env.example)
docker-compose up -d --build
docker-compose exec web python manage.py makemigrations #может не пригодиться
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py populate_db number #любое число, лучше 10-20
docker-compose exec web python manage.py createsuperuser
docker-compose down
(если после миграций и создания суперпользователя страница не грузится можно перезапустить: 
docker-compose down
docker-compose up -d
)
Вроде всё, надеюсь ничего не забыл

