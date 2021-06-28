#
# Build with:
#  docker-compose build
# Manually build with:
#  docker build -t ts_deps:0.1 -f Dockerfile .

FROM python:3.8.8

WORKDIR /tmp

RUN apt update && apt -y install \
    libgtk-3-dev \ 
    python-wxtools \
    unzip \
    wget \
    libnss3 \
      && apt clean && apt purge

COPY requirements.txt ./
RUN pip install --upgrade pip
# This will get the binaries instead of build from source which takes FOREVER
RUN pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/ wxPython
RUN pip install --no-cache-dir -r requirements.txt
