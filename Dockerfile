FROM centos:7

LABEL maintainer="Sergey A Bobkov <sbobkov@alfabank.ru>, Evgeniy N Mareev <emareev@alfabank.ru>"
ENV VERSION="1.1" \
    ML_DEPS="g++ gcc gfortran musl-dev python3-dev" \
    REDIS_VERSION=3.2 \
    REDIS_CONFIG="/redis.conf" \
    REDIS_DATA="/redis/data" \
    # you can change REDIS_CONFIG on start or copy another into root when you create Dockerfile FROM this
    LANG=C.UTF-8

RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum -y update && \
    yum -y install python36u python36u-libs python36u-devel python3 && \
    yum -y install gcc gcc-c++ wget && \
    yum -y install redis unixODBC && \
    curl https://packages.microsoft.com/config/rhel/7/prod.repo > /etc/yum.repos.d/mssql-release.repo && \
    yum remove unixODBC-utf16 unixODBC-utf16-devel && \
    ACCEPT_EULA=Y yum -y install msodbcsql17 && \
    ln -s /usr/bin/python3.6 /usr/bin/python3 && \
    python3 -m ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install numpy \
                pandas \
                scipy \
                scikit-learn \
                redis \
                pypyodbc \
                sqlalchemy \
                jaydebeapi \
                ibm_db==2.0.8a \
                ibm_db_sa && \
    yum remove -y gcc gcc-c++ && \
    yum clean packages && \
    yum clean headers && \
    yum clean metadata && \
    yum clean all && \
    rm -rf /var/cache/yum && \
    mkdir -p $REDIS_DATA && \
    chown redis:redis $REDIS_DATA


COPY ./redis.conf $REDIS_CONFIG
EXPOSE "6379:6379"
VOLUME $REDIS_DATA


COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# os.environ['MODELS_PATH'] should be used by your application
ENV MODELS_PATH="models_handler/models"
ENV DUMPS_PATH="models_handler/dumps"

RUN mkdir -p $MODELS_PATH && mkdir -p $DUMPS_PATH

#redis port exposed by parent
#web port initated here, but should be forwarded at run
EXPOSE 80

#redis data mounted by parent
VOLUME $MODELS_PATH
VOLUME $DUMPS_PATH

COPY . /

CMD redis-server $REDIS_CONFIG --dir $REDIS_DATA && python3.6 start.py

