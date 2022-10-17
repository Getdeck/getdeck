FROM mozilla/sops:v3-alpine AS sops

# from https://stackoverflow.com/questions/60298619/awscli-version-2-on-alpine-linux
FROM python:3.10.5-alpine as aws_builder

ARG AWS_CLI_VERSION=2.7.20
RUN apk add --no-cache git unzip groff build-base libffi-dev cmake
RUN git clone --single-branch --depth 1 -b ${AWS_CLI_VERSION} https://github.com/aws/aws-cli.git

WORKDIR aws-cli
RUN sed -i'' 's/PyInstaller.*/PyInstaller==5.2/g' requirements-build.txt
RUN python -m venv venv
RUN . venv/bin/activate
RUN scripts/installers/make-exe
RUN unzip -q dist/awscli-exe.zip
RUN aws/install --bin-dir /aws-cli-bin
RUN /aws-cli-bin/aws --version

# reduce image size: remove autocomplete and examples
RUN rm -rf /usr/local/aws-cli/v2/current/dist/aws_completer /usr/local/aws-cli/v2/current/dist/awscli/data/ac.index /usr/local/aws-cli/v2/current/dist/awscli/examples
RUN find /usr/local/aws-cli/v2/current/dist/awscli/botocore/data -name examples-1.json -delete

FROM alpine
LABEL maintainer="Schille"

ARG TARGETARCH
ARG HELM_VERSION=3.8.2
ARG KUBECTL_VERSION=1.23.5
ARG KUSTOMIZE_VERSION=v4.5.3
ARG KUBESEAL_VERSION=v0.15.0

# Install helm (latest release)
# ENV BASE_URL="https://storage.googleapis.com/kubernetes-helm"
ENV BASE_URL="https://get.helm.sh"
ENV TAR_FILE="helm-v${HELM_VERSION}-linux-${TARGETARCH}.tar.gz"
RUN apk add --update --no-cache curl ca-certificates tar bash git gnupg && \
    curl -sL ${BASE_URL}/${TAR_FILE} | tar -xvz && \
    mv linux-${TARGETARCH}/helm /usr/bin/helm && \
    chmod +x /usr/bin/helm && \
    rm -rf linux-${TARGETARCH}

ENV HELM_DATA_HOME=/usr/local/share/helm

COPY --from=aws_builder /usr/local/aws-cli/ /usr/local/aws-cli/
COPY --from=aws_builder /aws-cli-bin/ /usr/local/bin/
COPY --from=sops /usr/local/bin/sops /bin/sops



RUN helm repo add stable https://charts.helm.sh/stable \
    && helm repo add bitnami https://charts.bitnami.com/bitnami \
    && helm plugin install https://github.com/nico-ulbricht/helm-multivalues \
    && helm plugin install https://github.com/jkroepke/helm-secrets \
    && helm plugin install https://github.com/databus23/helm-diff && rm -rf /tmp/helm-* \
    && helm plugin install https://github.com/quintush/helm-unittest && rm -rf /tmp/helm-* \
    && helm plugin install https://github.com/chartmuseum/helm-push && rm -rf /tmp/helm-*

# Install kubectl
RUN curl -sLO https://storage.googleapis.com/kubernetes-release/release/v${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl && \
    mv kubectl /usr/bin/kubectl && \
    chmod +x /usr/bin/kubectl

# Install kustomize (latest release)
RUN curl -sLO https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_${TARGETARCH}.tar.gz && \
    tar xvzf kustomize_${KUSTOMIZE_VERSION}_linux_${TARGETARCH}.tar.gz && \
    mv kustomize /usr/bin/kustomize && \
    chmod +x /usr/bin/kustomize

# Install jq
RUN apk add --update --no-cache jq

# Install for envsubst
RUN apk add --update --no-cache gettext

# Install kubeseal
RUN curl -sL https://github.com/bitnami-labs/sealed-secrets/releases/download/${KUBESEAL_VERSION}/kubeseal-linux-${TARGETARCH} -o kubeseal && \
    mv kubeseal /usr/bin/kubeseal && \
    chmod +x /usr/bin/kubeseal


RUN mkdir /sources
WORKDIR /sources
RUN mkdir /output
