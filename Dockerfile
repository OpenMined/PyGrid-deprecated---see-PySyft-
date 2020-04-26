<<<<<<< HEAD
FROM python:3.7-slim
RUN apt-get update
RUN apt-get install -y git python3-pip python3-dev
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt
=======
FROM openmined/pysyft-lite as base

FROM base as builder

RUN apt-get update
RUN apt-get install -y git python3-pip python3-dev
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip3 install --user -r requirements.txt


FROM openmined/pysyft-lite as grid_app

COPY --from=builder root/.local root/.local

>>>>>>> f818247b25df9491cc3dbf87e15e064cbe979148
COPY . /app
WORKDIR /app
ENTRYPOINT ["sh", "entrypoint.sh"]
