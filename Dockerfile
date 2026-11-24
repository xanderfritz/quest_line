# small python base image (3.12 required for django 6.1)
FROM python:3.12-slim

# dont write pyc files, dont buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# use sqlite inside the container so no external db needed for the demo
ENV DB_ENGINE=sqlite
ENV DEBUG=True
ENV ALLOWED_HOSTS=*
ENV SECRET_KEY=docker-demo-key-change-me

# set the working folder inside the container
WORKDIR /app

# install deps first so docker caches this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the project
COPY . .

# run migrations so the sqlite db is ready to go
RUN python manage.py migrate --noinput

# open the django dev server port
EXPOSE 8000

# start the server listening on all interfaces so docker can map the port
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
