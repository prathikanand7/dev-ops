FROM jupyter/r-notebook:latest

USER root

# Install Papermill
RUN pip install papermill

# Copy the environment file into the container
COPY /inputs/environment.yaml /tmp/environment.yaml

# Update the Conda environment
RUN mamba env update --name base --file /tmp/environment.yaml && \
    mamba clean --all -f -y

# Set the working directory
WORKDIR /app

USER ${NB_UID}