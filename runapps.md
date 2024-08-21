## Django
>> gunicorn --pid=gunicorn.pid hello.wsgi:application -b 0.0.0.0:8080 -w 2

## flask
>> gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:5000 app:app

## fastapi
>> gunicorn app-orm:app -k uvicorn.workers.UvicornWorker --workers=2 --bind 0.0.0.0:8080

## express
>> node app.js

## fastify
>> node app.js

## gin-gorm
>> go run main.go