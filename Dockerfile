FROM python:3.11

RUN mkdir /docker-application
RUN mkdir /docker-application/SA
RUN mkdir /docker-application/src
RUN mkdir /docker-application/src/platform

WORKDIR /docker-application

COPY ./requirements.txt /docker-application/requirements.txt
COPY ./main.py /docker-application/main.py
COPY ./src /docker-application/src
COPY ./SA /docker-application/SA

ENV GOOGLE_APPLICATION_CREDENTIALS /docker-application/SA/service_account.json

RUN pip install update
RUN python -m pip install --upgrade pip
RUN pip install -r /docker-application/requirements.txt

CMD ["python3","main.py"]
docker push asia-southeast1-docker.pkg.dev/pnj-material-planing/docker-mrp-deployment/mrp-planning:0.0.1