## Create new virtual environment
>> python3 -m venv venv
>> source venv/bin/activate

## Django
>> gunicorn --pid=gunicorn.pid hello.wsgi:application -b 0.0.0.0:8080 -w 1

## flask
>> gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:8080 app:app

## fastapi
>> gunicorn app-orm:app -k uvicorn.workers.UvicornWorker --workers=1 --bind 0.0.0.0:8080

## express
>> cd express
>> npm install
>> node new-app.js

## fastify
>> cd fastify
>> npm install
>> node app.js

## gin-gorm
>> go run main.go