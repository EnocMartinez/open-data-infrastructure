#!/usr/bin/env python3
"""
Backups the SensorThings API database

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 16/11/23
"""

import os
import time
import rich
from argparse import ArgumentParser
try:
    from utils import setup_log, create_pgpass, container_get_ip, var_from_env_file, container_stop, container_start, PSQL
except ImportError:
    from scripts.utils import setup_log, create_pgpass, get_container_ip, var_from_env_file, container_stop

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("-v", "--verbose", action="store_true", help="Shows verbose output", default=False)
    argparser.add_argument("-l", "--logs", help="Logs folder", default="logs")
    argparser.add_argument("backup_file", type=str, help="Database dump file")
    args = argparser.parse_args()

    sensorthings_container = "sensorthings"
    sensorthings_db_container = "sta_db"
    sensorthings_network = f"{sensorthings_container}_default"

    env_file = "/etc/odi/secrets/sensorthings.env"

    log = setup_log("restore", "logs", logger_name="DB restorer")
    container_ip = container_get_ip(sensorthings_db_container, docker_network=sensorthings_network)
    create_pgpass(env_file, container_ip)

    db_user = var_from_env_file(env_file, "sta_db_user")
    db_name = var_from_env_file(env_file, "sta_db_name")
    db_port = var_from_env_file(env_file, "sta_db_port")
    db_pwd = var_from_env_file(env_file, "sta_db_password")

    # Postgres user
    pg_user = var_from_env_file(env_file, "POSTGRES_USER")
    pg_pwd = var_from_env_file(env_file, "POSTGRES_PASSWORD")

    # Readonly user
    ro_user = var_from_env_file(env_file, "sta_readonly_user")
    ro_pwd = var_from_env_file(env_file, "sta_readonly_password")

    psql = PSQL(container_ip, pg_user, db_port)

    init = time.time()
    rich.print("Starting dump...")

    dump_options = [
        "--format=plain",
        "--quote-all-identifiers",
        "--no-tablespaces",
        "--no-owner",
        "--no-privileges"
    ]
    dump_options = ["-Fc", "-b", "-v"]
    psql.dump(db_name, args.backup_file, dump_options, verbose=args.verbose)
    log.info("done")

    log.info("Starting container sensorthings...")
    container_start(sensorthings_container)
    log.info("started")
