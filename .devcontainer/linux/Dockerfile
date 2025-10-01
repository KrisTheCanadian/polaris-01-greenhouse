FROM python:3.13.7-bookworm

# Copy over the certs needed
COPY ./certs/ssl_proxy_corp_cse-cst_gc_ca.crt /usr/local/share/ca-certificates/ssl_proxy_corp_cse-cst_gc_ca.crt
COPY ./certs/perim-sslo-1.perimeter.cse-cst.gc.ca.crt /usr/local/share/ca-certificates/perim-sslo-1.perimeter.cse-cst.gc.ca.crt
COPY ./certs/perim-sslo-2.perimeter.cse-cst.gc.ca.crt /usr/local/share/ca-certificates/perim-sslo-2.perimeter.cse-cst.gc.ca.crt
COPY ./certs/perim-sslo-3.perimeter.cse-cst.gc.ca.crt /usr/local/share/ca-certificates/perim-sslo-3.perimeter.cse-cst.gc.ca.crt
COPY ./certs/s3bucketchaindev.crt /usr/local/share/ca-certificates/s3bucketchaindev.crt

# Copy over combined cert to .ssh
COPY ./certs/combined.crt /home/python/.ssh/combined.crt

RUN cat /usr/local/share/ca-certificates/ssl_proxy_corp_cse-cst_gc_ca.crt >> /etc/ssl/certs/ca-certificates.crt
RUN cat /usr/local/share/ca-certificates/perim-sslo-1.perimeter.cse-cst.gc.ca.crt >> /etc/ssl/certs/ca-certificates.crt
RUN cat /usr/local/share/ca-certificates/perim-sslo-2.perimeter.cse-cst.gc.ca.crt >> /etc/ssl/certs/ca-certificates.crt
RUN cat /usr/local/share/ca-certificates/perim-sslo-3.perimeter.cse-cst.gc.ca.crt >> /etc/ssl/certs/ca-certificates.crt
RUN cat /usr/local/share/ca-certificates/s3bucketchaindev.crt >> /etc/ssl/certs/ca-certificates.crt

# Update trusted certificates
RUN update-ca-certificates

# Install SUDO
RUN apt-get update && apt-get install -y sudo apt-transport-https gnupg2 curl

RUN install -m 0755 -d /etc/apt/keyrings

# Create a group and user for python
RUN addgroup --gid 1000 python_group \
    && adduser --disabled-password --gecos '' --uid 1000 --gid 1000 python

# Allow the python user to run sudo commands without password
RUN echo "python ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Set the working directory
WORKDIR /home/python/workspace

# Copy necessary files and set permissions
RUN chown -R python:python_group /home/python/

# Command to run on container startup
CMD ["/bin/bash", "-c", "sleep infinity"]