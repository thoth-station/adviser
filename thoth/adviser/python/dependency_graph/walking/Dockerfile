FROM centos:7

RUN yum install -y gcc-c++ make && mkdir /home/buildroot/
COPY ./ /home/buildroot
RUN cd /home/buildroot && make clean && make
