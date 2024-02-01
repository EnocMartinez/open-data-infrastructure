#!/usr/bin/env python3
"""

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 3/11/23
"""

import os
import rich
import yaml


os.chdir("..")
directories = [d for d in os.listdir(".") if os.path.isdir(d)]  # get directories
# Now get all docker compose files

for directory in directories:
    compose_file = os.path.join(directory, "docker-compose.yaml")
    if not os.path.exists(compose_file):
        rich.print(f"Folder {directory} does not contain a docker compose, skip")
        continue

    rich.print(f"Processing {compose_file}")
    with open(compose_file) as f:
        compose = yaml.safe_load(f)

    for name, service in compose["services"].items():
        if "volumes" not in service.keys():
            rich.print(f"[grey]Container '{directory}:{name}' does not have container")
            continue

        rich.print(f"\n[purple]processing containers for '{directory}:{name}'")
        for volume in service["volumes"]:
            try:
                source, destination = volume.split(":") # split src:dest
            except ValueError:
                source, destination, permissions = volume.split(":")   # split src:dest:permissions

            if not source.startswith("../../volumes"):
                rich.print(f"volume {source} not following ODI conventions, skipping")
            elif "." not in source.split("/")[-1]:
                os.chdir(directory)
                rich.print(f"[green]    creating {source}")
                os.system(f"mkdir -p {source}")
                os.system(f"chmod 777 {source}")
                os.chdir("..")
            else:
                rich.print(f"[grey]ignoring {source}, assuming its a file")


