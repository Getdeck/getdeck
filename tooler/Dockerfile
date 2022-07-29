FROM mozilla/sops:v3-alpine AS sops

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
