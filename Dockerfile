ARG QGIS_TEST_VERSION=latest
FROM  qgis/qgis:${QGIS_TEST_VERSION}
MAINTAINER Germán Carrillo <gcarrillo@linuxmail.org>

RUN apt-get update && \
    apt-get -y install \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

COPY ./ /usr/src/

RUN chmod a+x /usr/src/run-docker-tests.sh

WORKDIR /
