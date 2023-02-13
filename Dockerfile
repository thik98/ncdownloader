FROM ubuntu:focal
ENV DEBIAN_FRONTEND=noninteractive

RUN set -x && \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install apt-utils locales gnupg \
    ca-certificates language-pack-ja tzdata \
    python3 python3-pip python3-setuptools \
    git make g++ yasm vim less curl cron \
    libfdk-aac-dev \
    libva-dev vainfo i965-va-driver \
    libmfx-dev intel-media-va-driver-non-free

ENV TZ=Asia/Tokyo
ENV LANG=ja_JP.UTF-8
ENV LANGUAGE=ja_JP:ja
ENV LC_ALL=ja_JP.UTF-8
ENV TERM xterm

RUN mkdir -p /root/src
COPY requirements.txt /root/src

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r /root/src/requirements.txt

RUN set -x && \
    mkdir /opt/ffmpeg && \
    cd /opt/ffmpeg && \
    git clone https://github.com/FFmpeg/FFmpeg --depth=1 -b n4.3.1 . && \
    ./configure \
      --enable-libfdk-aac \
      --disable-ffplay \
      --disable-debug \
      --disable-doc \
      --enable-libmfx && \
    make -j $(grep cpu.cores /proc/cpuinfo | sort -u | sed 's/[^0-9]//g') && \
    make install

COPY execron.sh /
COPY ncdlcron /etc/cron.d/ncdlcron
RUN chmod 0644 /etc/cron.d/ncdlcron
RUN /usr/bin/crontab /etc/cron.d/ncdlcron
WORKDIR /root/src
CMD ["/bin/bash", "/execron.sh"]
