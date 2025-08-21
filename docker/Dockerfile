FROM python-base:v1

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 软连接python-> python3
RUN ln -s /usr/local/bin/python3 /usr/local/bin/python

RUN mkdir -p /root/workspace 
RUN mkdir -p /root/libtmp
COPY ./ /root/libtmp

WORKDIR /root/libtmp

RUN pip install -r ./docker/requirements.txt

RUN pip install .

RUN rm -rf /root/libtmp

WORKDIR /root/workspace

CMD ["bash"]