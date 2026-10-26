ARG BUILD_FROM
FROM node:24-alpine AS web-build
ARG WEB_REF=main
RUN apk add --no-cache curl tar python3
WORKDIR /web
RUN curl -fL --retry 3 \
      "https://codeload.github.com/rclone/rclone-web/tar.gz/${WEB_REF}" \
      -o /tmp/web.tar.gz \
    && tar -xzf /tmp/web.tar.gz --strip-components=1 -C /web \
    && rm /tmp/web.tar.gz
COPY patch_web.py ingress-bootstrap.html /patch/
RUN python3 /patch/patch_web.py \
    && npm ci \
    && npm run build -- --base ./ \
    && test -f dist/index.html

FROM golang:1.26-alpine AS scheduler-build
ARG UPSTREAM_REF=main
ARG BUILD_ARCH
RUN apk add --no-cache curl tar
WORKDIR /src
# Download upstream sources and notices at build time, not at runtime.
RUN curl -fL --retry 3 \
      "https://codeload.github.com/jcwillox/hassio-rclone-backup/tar.gz/${UPSTREAM_REF}" \
      -o /tmp/upstream.tar.gz \
    && tar -xzf /tmp/upstream.tar.gz --strip-components=1 -C /src \
    && rm /tmp/upstream.tar.gz
WORKDIR /src/rclone_backup/scheduler
RUN set -eu; \
    case "${BUILD_ARCH}" in \
      amd64) export GOARCH=amd64 ;; \
      aarch64) export GOARCH=arm64 ;; \
      armhf) export GOARCH=arm GOARM=6 ;; \
      armv7) export GOARCH=arm GOARM=7 ;; \
      i386) export GOARCH=386 ;; \
      *) echo "Unsupported architecture" >&2; exit 1 ;; \
    esac; \
    CGO_ENABLED=0 go build -trimpath -o /out/scheduler .

FROM ${BUILD_FROM}
ARG BUILD_ARCH
ARG BUILD_VERSION
ARG RCLONE_REFRESH=initial
ENV LANG=C.UTF-8
RUN apk add --no-cache curl unzip nginx fuse \
    && sed -i 's/#user_allow_other/user_allow_other/' /etc/fuse.conf \
    && ln -sf /bin/fusermount /bin/fusermount3

# Use one version-specific archive and its official checksum manifest.
# RCLONE_REFRESH invalidates the Docker cache for subsequent updates.
RUN set -eu; \
    echo "Rclone refresh: ${RCLONE_REFRESH}"; \
    case "${BUILD_ARCH}" in \
      amd64) arch=amd64 ;; \
      aarch64) arch=arm64 ;; \
      armhf) arch=arm-v6 ;; \
      armv7) arch=arm-v7 ;; \
      i386) arch=386 ;; \
      *) echo "Unsupported architecture" >&2; exit 1 ;; \
    esac; \
    version="$(curl -fL --retry 3 https://downloads.rclone.org/version.txt | awk '{print $2}')"; \
    case "${version}" in v[0-9]*.[0-9]*.[0-9]*) ;; *) exit 1 ;; esac; \
    archive="rclone-${version}-linux-${arch}.zip"; \
    mkdir -p /tmp/rclone-install /usr/share/rclone-backup-web /root/.config/rclone; \
    cd /tmp/rclone-install; \
    curl -fL --retry 3 "https://downloads.rclone.org/${version}/${archive}" -o "${archive}"; \
    curl -fL --retry 3 "https://downloads.rclone.org/${version}/SHA256SUMS" -o SHA256SUMS; \
    awk -v wanted="${archive}" '{name=$2; sub(/^\*/, "", name); if(name==wanted) print $0}' SHA256SUMS > selected.sha256; \
    test -s selected.sha256; \
    sha256sum -c selected.sha256; \
    unzip -q "${archive}"; \
    cp "rclone-${version}-linux-${arch}/rclone" /usr/bin/rclone; \
    chmod 755 /usr/bin/rclone; \
    /usr/bin/rclone version; \
    /usr/bin/rclone gui --help >/dev/null; \
    printf '%s\n' "${version}" > /usr/share/rclone-backup-web/rclone-version; \
    cd /; rm -rf /tmp/rclone-install

# Retain upstream initialization and service supervision, then override our files.
COPY --from=scheduler-build /src/rclone_backup/rootfs/ /
COPY --from=scheduler-build /src/LICENSE /usr/share/licenses/upstream-scheduler/LICENSE
COPY --from=scheduler-build /out/scheduler /usr/bin/scheduler
COPY --from=web-build /web/dist/ /usr/share/rclone-web/
COPY --from=web-build /web/LICENSE /usr/share/licenses/rclone-web/LICENSE
COPY rootfs/ /
RUN chmod a+x /etc/cont-init.d/* /etc/services.d/*/* \
    && mkdir -p /run/nginx \
    && grep -q __HA_BASE_PLACEHOLDER__ /usr/share/rclone-web/index.html \
    && nginx -t
LABEL io.hass.type="addon" io.hass.arch="${BUILD_ARCH}" io.hass.version="${BUILD_VERSION}"
