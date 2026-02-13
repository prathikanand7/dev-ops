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

# Copy scripts and files
# This includes the given env as a base
# TODO: We must check if we can use another env that is common for ERIC?
COPY . /app 

RUN chown -R ${NB_UID} /app

USER ${NB_UID}