FROM jupyter/r-notebook:latest

USER root

WORKDIR /app

COPY /inputs/environment.yaml ./environment.yaml

# Update the Conda environment
RUN mamba env update --name base --file ./environment.yaml && \
    mamba clean --all -f -y && \
    pip install --no-cache-dir papermill==2.6.0

COPY . /app

RUN chown -R ${NB_UID} /app

USER ${NB_UID}