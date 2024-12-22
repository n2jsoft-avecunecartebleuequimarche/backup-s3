FROM alpine:3.7

ENV QUEUE=myqueue
ENV ENDPOINT=http://localstack:4566

COPY wait.sh /wait.sh
RUN apk add --no-cache curl && chmod +x wait.sh

CMD ["/wait.sh"]




