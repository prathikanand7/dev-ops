FROM jupyter/r-notebook:latest

USER root

WORKDIR /app

COPY inputs/environment.yaml ./environment.yaml

RUN mamba env update --name base --file ./environment.yaml && \
    mamba clean --all -f -y && \
    pip install --no-cache-dir papermill==2.6.0 boto3==1.34.*

COPY . /app

RUN chown -R ${NB_UID} /app

USER ${NB_UID}

CMD ["python", "worker.py"]