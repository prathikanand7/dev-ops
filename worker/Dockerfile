FROM jupyter/r-notebook:latest

USER root

WORKDIR /app

COPY /inputs/environment.yaml ./environment.yaml

# 2. Update the Conda environment
RUN mamba env update --name base --file ./environment.yaml && \
    mamba clean --all -f -y && \
    pip install --no-cache-dir papermill==2.6.0

COPY --chown=${NB_UID}:users . /app 

USER ${NB_UID}

# TODO: We must check if we can use another env that is common for ERIC?
