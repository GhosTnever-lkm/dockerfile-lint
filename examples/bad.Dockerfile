FROM ubuntu:latest
ENV API_TOKEN=abc123
ADD app.tar.gz /opt/
RUN curl -fsSL https://example.com/install.sh | sh
RUN apt-get install -y git
CMD ["./run"]
CMD ["./run2"]
