FROM postgres:17.0-alpine3.20 as build
FROM scratch as postgres
COPY --from=build / /
ENV PG_MAJOR=17
ENV LANG=en_US.utf8
ENV PG_VERSION=17.0
ENV GOSU_VERSION=1.17
ENV BB_ASH_VERSION=1.36.1
ENV PGDATA=/var/lib/postgresql/data
ENV DOCKER_PG_LLVM_DEPS="lvm15-dev 		clang15"
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV PG_SHA256=7e276131c0fdd6b62588dbad9b3bb24b8c3498d5009328dba59af16e819109de

STOPSIGNAL SIGINT
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]
