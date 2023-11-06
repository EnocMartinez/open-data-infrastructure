#!/usr/bin/env python3
"""
Start all containers that should run in this host

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 5/11/23
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
    argparser.add_argument("-i", "--infrastructure", help="Path no infrastructure.yaml", type=str, default="../secrets/infrastructure.yaml")
    argparser.add_argument("action", help="Docker action (up / down / start /stop)", type=str)

    __valid_actions = ["up", "down", "start", "stop"]

    args = argparser.parse_args()

    if args.action.lower() not in __valid_actions:
        rich.print(f"[red]ERROR: Actino not valid, expected one of {__valid_actions}")
        exit(1)


    action = args.action.lower()
    if action == "up":
        action += " --detach"  # add detach to up
    elif action == "down":
        action += " --remove-orphans"  # add remove orphans

    if not os.path.exists(args.infrastructure):
        rich.print(f"[red]ERROR: Infrastructure file does not exist (path {args.infrastructure})\n")
        exit(1)

    with open(args.infrastructure) as f:
        infrastructure = yaml.safe_load(f)["infrastructure"]

    hostname = os.uname().nodename

    services = [s.split(":") for s in infrastructure["services"]]
    # Check that all

    wdir = os.getcwd()
    for service, host in services:
        if host == hostname:
            try:
                os.chdir(service)
            except FileNotFoundError:
                rich.print(f"[red]ERROR! folder {service} does not exist! skipping action")
            cmd = f"docker compose {action}"
            rich.print(f"\n==> Service '{service}' running '{cmd}'...")
            ret = os.system(cmd)
            if ret == 0:
                rich.print(f"{service}...[green]ok!")
            else:
                rich.print(f"{service}...[red]failed")
            os.chdir(wdir)
        else:
            rich.print(f"[blue]skipping service {service}...")


