FROM amazonlinux:latest

RUN yum -y update
RUN yum install python-dev python-pip -y

#RUN yum  clean all
#RUN amazon-linux-extras enable python3.8
#RUN yum install python3.8 -y
#
RUN pip install awscli
#
## following to support ecs task role
#RUN yum install -y sudo
#RUN cat /etc/os-release
# end

WORKDIR /tmp/workdir
#
COPY copy_outfile.sh /tmp/workdir
COPY copy_infile.sh /tmp/workdir
#
RUN sed -i -e 's/\r$//' /tmp/workdir/copy_outfile.sh
RUN sed -i -e 's/\r$//' /tmp/workdir/copy_infile.sh

RUN chmod 755 -R /tmp/workdir
ENTRYPOINT ./copy_infile.sh && ./copy_outfile.sh
