FROM jupyter/datascience-notebook:latest

USER root
WORKDIR /app

RUN pip install --no-cache-dir papermill==2.6.0 boto3==1.34.*

COPY . /app
RUN chown -R ${NB_UID} /app
USER ${NB_UID}

CMD ["python", "worker.py"]
