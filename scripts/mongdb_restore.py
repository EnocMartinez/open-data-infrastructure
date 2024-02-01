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
import rich
try:
    from utils import setup_log, var_from_env_file, container_put_file, container_exec
except ImportError:
    from scripts.utils import setup_log, var_from_env_file, container_put_file, container_exec


if __name__ == "__main__":

    argparser = ArgumentParser()
    argparser.add_argument("-l", "--logs", help="Logs folder", default="logs")
    argparser.add_argument("backup_file", type=str, help="Database folder")
    args = argparser.parse_args()

    log = setup_log("Restore MongoDB", "logs")

    if not os.path.isfile(args.backup_file):
        log.error(f"backup file not found {args.backup_file}")
        raise FileNotFoundError(f"backup file not found {args.backup_file}")


    env_file = "/etc/odi/secrets/mmapi.env"
    container_name = "mmapi-db2"

    now = datetime.utcnow().strftime(f"%Y%m%d_%H%M%S")
    conn = var_from_env_file(env_file, "mongodb_connection")

    # Extract username and password from the mongo connection string
    username = conn.split("//")[1].split(":")[0]
    password = conn.split(":")[2].split("@")[0]
    log.info(f"Copy backup {args.backup_file} to container...")
    backup = f"/tmp/{os.path.basename(args.backup_file)}"
    os.system(f"docker cp {args.backup_file} {container_name}:{backup}")

    log.info("Running mongorestore command")
    cmd = f'mongorestore  --username="{username}" --password="{password}" --port=27017 '\
           f'--host=127.0.0.1 --authenticationDatabase=admin --archive="{backup}"'
    print(cmd)
    code, output = container_exec(container_name, cmd)

    import rich
    if code != 0:
        print(f"code {code}")
        rich.print(output.decode())
        exit()

    code, output = container_exec(container_name, f"rm {backup}")
    log.info("restore complete!")

