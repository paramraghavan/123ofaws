# docker + flask webserver
- https://docs.docker.com/language/python/build-images/

 pip install Flask

 pip freeze > requirements.txt

 touch app.py
<pre>
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello_world():
        return 'Hello, Docker!'
</pre>

python -m flask run

Dockerfile
------------
<pre>
# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY app.py .
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
</pre>

- docker build -t pyflask-docker .
- docker run pyflask-docker
- https://docs.docker.com/language/python/run-containers/
<pre>
To publish a port for our container, we’ll use the --publish flag (-p for short) 
on the docker run command. The format of the --publish command is [host port]:[container port]. 
So, if we wanted to expose port 5000 inside the container to port 3000 outside 
the container, we would pass 3000:5000 to the --publish flag.
We did not specify a port when running the flask application in the container and 
the default is 5000. If we want our previous request going to port 5000 to work we can map the
host’s port 5000 to the container’s port 5000:

docker run --publish 8000:5000 pyflask-docker
</pre>

- Docker - Bind for 0.0.0.0:4000 failed: port is already allocated
<pre>
Fix:
docker container ls
docker rm -f <container-name>
ref: https://stackoverflow.com/questions/46176584/docker-bind-for-0-0-0-04000-failed-port-is-already-allocated
</pre>

- deploy app to minikube