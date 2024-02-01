#!/usr/bin/env python3
"""
Restores SensorThings Database and transfers it to a remote server

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 21/06/2022
"""

import os
import time
import rich
from argparse import ArgumentParser
try:
    from utils import setup_log, create_pgpass, container_get_ip, var_from_env_file, container_stop, container_start, PSQL
except ImportError:
    from scripts.utils import setup_log, create_pgpass, get_container_ip, var_from_env_file, container_stop


def command(cmd, allow_fail=False):
    import rich
    rich.print(f"[magenta]{cmd}")
    r = os.system(cmd)
    if r != 0:
        if allow_fail:
            log.warning(f"command \"{cmd}\" failed!")
        else:
            log.error(f"command \"{cmd}\" failed!")
            exit()

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("-v", "--verbose", action="store_true", help="Shows verbose output", default=False)
    argparser.add_argument("-l", "--logs", help="Logs folder", default="logs")
    argparser.add_argument("backup_file", type=str, help="Database dump file")
    args = argparser.parse_args()

    log = setup_log("restore", "logs", logger_name="DB restorer")

    containers = ["sensorthings2"]#, "sta-timeseries", "pgadmin"]
    for container in containers:
        log.info(f"Stopping container {container}...")
        container_stop(container)


    #container_ip = container_get_ip("sta_db", docker_network="sensorthings-net")
    container_ip = container_get_ip("sta_db2", docker_network="sensorthings2_default")

    rich.print(f"sta_db container ip: {container_ip}")
    create_pgpass("/etc/odi/secrets/sensorthings.env", container_ip)

    # if args.verbose:
    #     logging.setLevel(logging.DEBUG)
    env_file = "/etc/odi/secrets/sensorthings.env"
    # SensorThings Database
    db_user = var_from_env_file(env_file, "sta_db_user")
    db_name = var_from_env_file(env_file, "sta_db_name")
    db_port =  var_from_env_file(env_file, "sta_db_port")
    db_pwd = var_from_env_file(env_file, "sta_db_password")

    # Postgres user
    pg_user = var_from_env_file(env_file, "POSTGRES_USER")
    pg_pwd = var_from_env_file(env_file, "POSTGRES_PASSWORD")

    # Readonly user
    ro_user = var_from_env_file(env_file, "sta_readonly_user")
    ro_pwd = var_from_env_file(env_file, "sta_readonly_password")

    psql = PSQL(container_ip, pg_user, db_port)

    init = time.time()
    log.info(f"Dropping existing database...")
    psql.run(f"select pg_terminate_backend(pid) from pg_stat_activity where datname='{db_name}';", allow_fail=True, verbose=True)
    psql.run(f"DROP DATABASE {db_name};", allow_fail=True, verbose=args.verbose)
    # command(f'psql --host {container_ip} -U sensorthings -p {db_port} -c "DROP sensorthingsSELECT timescaledb_pre_restore();" {db_name}')

    #psql.run(f"CREATE ROLE {db_user} WITH LOGIN CREATEDB PASSWORD '{db_pwd}' SUPERUSER;", allow_fail=True)
    #psql.run(f"CREATE ROLE {ro_user} WITH LOGIN CREATEDB PASSWORD '{ro_pwd}';", allow_fail=True)
    psql.run(f"CREATE DATABASE {db_name};", verbose=args.verbose)
    psql.run(f"CREATE EXTENSION IF NOT EXISTS postgis;", db_name, verbose=args.verbose )
    psql.run(f"CREATE EXTENSION IF NOT EXISTS timescaledb;", db_name, verbose=args.verbose)
    # psql.run(f"SELECT timescaledb_pre_restore();", db_name)
    # t = time.time()
    # command(f'pg_restore --host {container_ip} -U {db_user} -Fc -d {db_name} {args.backup_file}')
    # psql.run(f"SELECT timescaledb_post_restore();", db_name)

    psql.run(f"SELECT timescaledb_pre_restore();", verbose=args.verbose)
    #psql.file(args.backup_file, db_name, verbose=args.verbose)
    options = ["-Fc",  "-v"]
    psql.restore(db_name, args.backup_file, options, verbose=args.verbose)
    psql.run(f"SELECT timescaledb_post_restore();", verbose=args.verbose)

    log.info(f"Total restore time {time.time() - init: .04f} seconds")
    log.info("done")

    log.info("Starting container sensorthings...")
    [container_start(cont) for cont in containers]
    log.info("started")



