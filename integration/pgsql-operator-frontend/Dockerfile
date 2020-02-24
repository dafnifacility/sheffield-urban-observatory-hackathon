FROM ubuntu
COPY static static
COPY kpgfrontend /frontend
RUN apt-get update && apt-get -y install curl && curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl && mv kubectl /usr/local/bin && chmod +x /usr/local/bin/kubectl
ENTRYPOINT ["/frontend"]
