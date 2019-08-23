# Use a LTS Ubuntu version as parent image
FROM ubuntu:18.04

ENV  BUILD_DIR /opt/chado-tools

# Install dependencies (Python and postgresql)
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3.6 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    postgresql \
    postgresql-client \
    postgresql-contrib \
    libpq-dev \
    gcc

# Copy repo content into container
RUN  mkdir -p ${BUILD_DIR}
COPY . ${BUILD_DIR}

# Install chado-tools
RUN pip3 install wheel && \
    pip3 install ${BUILD_DIR}

# Define the default command
CMD echo "Usage: docker run --rm -it <IMAGE_NAME> chado -h"

#Metadata
LABEL maintainer "path-help@sanger.ac.uk"