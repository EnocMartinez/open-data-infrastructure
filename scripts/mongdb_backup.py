#!/usr/bin/env python3
"""
Dumps a MongoDB database

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 19/1/24
"""

from argparse import ArgumentParser
import os
from datetime import datetime

try:
    from utils import setup_log, var_from_env_file, container_get_file, container_exec
except ImportError:
    from scripts.utils import setup_log, var_from_env_file, container_get_archive, container_exec


if __name__ == "__main__":

    argparser = ArgumentParser()
    argparser.add_argument("-l", "--logs", help="Logs folder", default="logs")
    argparser.add_argument("backup_folder", type=str, help="Database folder")
    args = argparser.parse_args()

    log = setup_log("Backup MongoDB", "logs")

    env_file = "/etc/odi/secrets/mmapi.env"
    container_name = "mmapi-db"

    now = datetime.utcnow().strftime(f"%Y%m%d_%H%M%S")
    conn = var_from_env_file(env_file, "mongodb_connection")

    # Extract username and password from the mongo connection string
    username = conn.split("//")[1].split(":")[0]
    password = conn.split(":")[2].split("@")[0]

    os.makedirs(args.backup_folder, exist_ok=True)
    archive_name = f"/tmp/mmapi_db_{now}"
    destination = os.path.join(args.backup_folder, f"mmapi_db_{now}")
    log.info(f"Archive name {archive_name}")
    log.info("Running mongodump command")
    cmd = f'mongodump  --username="{username}" --password="{password}"  --port=27017 --host=127.0.0.1 ' \
          f'--authenticationDatabase=admin --archive="{archive_name}"'
    code, output = container_exec(container_name, cmd)
    if code != 0:
        log.error(f"status code: {code}")
        log.error(f"docker exec output\n------------\n{output.decode()}------------")
        raise ValueError("Docker exec error, check logs")

    log.info("backup successful!")
    log.info(f"Copy dump from container to {destination}")
    #container_get_file(container_name, archive_name, destination)
    os.system(f"docker cp {container_name}:{archive_name} {destination}")
    # log.info("Deleting dump inside container...")
    # code, output = container_exec(container_name, f"rm {archive_name}")
    log.info("backup complete!")

    print(f"to restore: ./mongdb_restore.py {destination}")

