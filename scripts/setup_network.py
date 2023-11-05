#!/usr/bin/env python3
"""
This script sets up all the required rules for iptables in the ODI entry point (the VM running the nginx reverse proxy)

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 3/11/23
"""
import yaml
import rich
import os
from argparse import ArgumentParser

def start_service(service):
    if not os.path.isdir(service):
        rich.print(f"[red]ERROR: folder '{service}' does not exist!")
        exit(1)

    os.chdir(service)
    rich.print(f"Starting service '{service}'...")
    rich.print("docker compose up -d")
    os.chdir("..")

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("-i", "--infrastructure", help="Path no infrastructure.yaml", type=str, default="../../secrets/infrastructure.yaml")
    args = argparser.parse_args()

    if not os.path.exists(args.infrastructure):
        rich.print(f"[red]ERROR: Infrastructure file does not exist (path {args.infrastructure})\n")
        exit(1)

    with open(args.infrastructure) as f:
        network = yaml.safe_load(f)

    rich.print(network)
    hostname = os.uname().nodename
    services = {s.split(":")[0]: s.split(":")[1] for s in network["infrastructure"]["services"]}

    if hostname != services["proxy"]:
        rich.print(f"[red]ERROR! This machine is not the entry point, the configured entry point is '{services['proxy']}'")
        exit(1)

    # Check that all
    for service, host in services:
        if host == hostname:
            rich.print(f"Starting service {service}...")
        else:
            rich.print(f"Skipping service {service}, ({host} != {hostname})...")


