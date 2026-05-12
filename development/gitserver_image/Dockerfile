FROM node:alpine

RUN apk add --no-cache tini git \
    && yarn global add git-http-server \
    && adduser -D -g git git

WORKDIR /home/git

COPY git_setup.sh /usr/local/bin/git_setup.sh
COPY repos/ /tmp/repos/
RUN chmod +x /usr/local/bin/git_setup.sh

USER git

ENTRYPOINT ["tini", "--", "/usr/local/bin/git_setup.sh"]