FROM python:3.7-slim as base

FROM base as builder

RUN apt-get update
RUN apt-get install -y git python3-pip python3-dev
COPY ./pip-dep /app/pip-dep

WORKDIR /app
RUN pip3 install --user -r pip-dep/requirements.txt


FROM python:3.7-slim as grid_app

COPY --from=builder root/.local root/.local

COPY . /app
WORKDIR /app
ENTRYPOINT ["sh", "entrypoint.sh"]

