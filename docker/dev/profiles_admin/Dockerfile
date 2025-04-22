FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/opt/profiles_admin


ARG GID=1000
ARG UID=1000
ARG USER=ubuntu

RUN apk add --update --no-cache python3-dev postgresql-dev curl gettext nginx && \
    addgroup -g $GID -S $USER && \
    adduser -S $USER -G $USER --uid "$UID" && \
    mkdir -p /django_gunicorn_socket && \
    chmod -R 755 /django_gunicorn_socket && \
    chown -R $USER:$USER /django_gunicorn_socket

# для логов
RUN mkdir -p /var/log/nginx/ && \
    chmod -R 777 /var/log/nginx/ && \
    chown -R $USER:$USER /var/log/nginx/

WORKDIR $APP_HOME

COPY --chown=$USER:$USER ./docker/dev/profiles_admin/entrypoints/entrypoint.sh /
COPY ./docker/dev/profiles_admin/nginx/conf.d /etc/nginx/conf.d
COPY ./docker/dev/profiles_admin/nginx/nginx.conf /etc/nginx/nginx.conf
COPY --chown=$USER:$USER ./profiles_admin $APP_HOME

RUN pip install --upgrade pip setuptools && \
    pip install --editable .[prod]

RUN chmod +x /*.sh && \
    mkdir -p media && \
    python manage.py collectstatic --no-input && \
    chown -R $USER:$USER $APP_HOME media && \
    chown -R $USER:$USER /etc/nginx /var/lib/nginx/ /var/log /run/nginx/

ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "src.asgi:application"]

EXPOSE 8000

USER $USER