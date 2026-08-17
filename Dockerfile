FROM alpine:3.20 AS build
ARG HUGO_VERSION=0.165.0
ARG BUILD_DRAFTS=false
RUN apk add --no-cache curl libc6-compat libstdc++ \
    && curl -sL -o /tmp/hugo.tar.gz "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz" \
    && tar -xzf /tmp/hugo.tar.gz -C /usr/local/bin hugo \
    && chmod +x /usr/local/bin/hugo \
    && rm /tmp/hugo.tar.gz \
    && hugo version
WORKDIR /src
COPY . .
RUN if [ "$BUILD_DRAFTS" = "true" ]; then hugo --buildDrafts; else hugo; fi

FROM nginx:alpine
COPY --from=build /src/public /usr/share/nginx/html
EXPOSE 80
