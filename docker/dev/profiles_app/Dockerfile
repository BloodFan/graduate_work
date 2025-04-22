FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/opt/profiles_app

ARG GID=1000
ARG UID=1000
ARG USER=ubuntu

RUN apk add --update --no-cache python3-dev curl nginx && \
    addgroup -g $GID -S $USER && \
    adduser -S $USER -G $USER --uid "$UID" && \
    mkdir -p /redis_socket && \
    chmod -R 777 /redis_socket && \
    chown -R $USER:$USER /redis_socket && \
    mkdir -p /profiles_app_gunicorn_socket && \
    chmod -R 755 /profiles_app_gunicorn_socket && \
    chown -R $USER:$USER /profiles_app_gunicorn_socket && \
    mkdir -p /var/log/profiles_app && \
    chmod -R 755 /var/log/profiles_app && \
    chown -R $USER:$USER /var/log/profiles_app
# для логов
RUN mkdir -p /var/log/nginx/ && \
    chmod -R 777 /var/log/nginx/ && \
    chown -R $USER:$USER /var/log/nginx/

WORKDIR $APP_HOME

COPY --chown=$USER:$USER ./docker/dev/profiles_app/entrypoints/entrypoint.sh /
COPY ./docker/dev/profiles_app/nginx/conf.d /etc/nginx/conf.d
COPY ./docker/dev/profiles_app/nginx/nginx.conf /etc/nginx/nginx.conf
COPY --chown=$USER:$USER ./profiles_app $APP_HOME

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install -r $APP_HOME/requirements/dev.txt


RUN chmod +x /*.sh && \
    chown -R $USER:$USER /etc/nginx /var/lib/nginx/ /var/log /run/nginx/

ENTRYPOINT ["/entrypoint.sh"]


# не забыть про сокет docker\dev\profiles_app\nginx\conf.d\default.conf
# CMD ["gunicorn", "-c", "gunicorn.conf.py", "src.main:app"]

# Для тестирования и разработки
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]

EXPOSE 9000

USER $USER
