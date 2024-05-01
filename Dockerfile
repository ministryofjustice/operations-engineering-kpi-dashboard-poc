FROM python:3.12.0-slim

LABEL maintainer="operations-engineering <operations-engineering@digital.justice.gov.uk>"

WORKDIR /home/operations-engineering-kpi-dashboard

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
COPY app app
COPY data data


RUN pip3 install --no-cache-dir pipenv
RUN pipenv install --system --deploy --ignore-pipfile

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 4567

ENTRYPOINT ["gunicorn", "--bind=0.0.0.0:4567", "app.run:app()"]
