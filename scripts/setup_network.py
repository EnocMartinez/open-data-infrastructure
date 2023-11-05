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
    argparser.add_argument("-f", "--force", action="store_true", help="If set, the script will skip the proxy machine check")
    argparser.add_argument("-s", "--script", type=str, help="path to add_nat_rule.sh script", default="./add_nat_rule.sh")
    args = argparser.parse_args()

    if not os.path.exists(args.infrastructure):
        rich.print(f"[red]ERROR: Infrastructure file does not exist (path {args.infrastructure})\n")
        exit(1)

    if not os.path.isfile(args.script):
        rich.print(f"[red]ERROR: add_nat_rule.sh not found (path {args.script})\n")
        exit(1)

    with open(args.infrastructure) as f:
        infrastructure = yaml.safe_load(f)["infrastructure"]

    hostname = os.uname().nodename
    services = {s.split(":")[0]: s.split(":")[1] for s in infrastructure["services"]}


    # rich.print("Registering servers in /etc/hosts")
    # with open("/etc/hosts") as f:
    #     hosts_contents = f.read().splitlines()
    # rich.print(hosts_contents)
    #
    # for address in infrastructure["addresses"]:
    #     rich.print(f"processing {address}")
    #     new_name, new_ip = address.split("=")
    #
    #     # Check if they already exist in /etc/hosts
    #     existing = False
    #     for hosts in hosts_contents:
    #         if not hosts or hosts.startswith("#"):
    #             continue
    #         hosts_ip = hosts.split()[0]
    #         hosts_names = hosts.split()[1:]
    #         if new_name in hosts_names:
    #             existing = True
    #             # Host already registered
    #             if hosts_ip == new_ip:
    #                 rich.print(f"Address {new_name} {new_ip} already registered")
    #             else: # update the host
    #                 rich.print(f"Updating {new_name} from {hosts_ip} to '{new_ip}'")
    #                 cmd = f"sudo su -c \"sed -i 's|{hosts}|{new_name} {new_ip}|g' /etc/hosts\""
    #                 print(cmd)
    #                 os.system(cmd)
    #     if not existing:
    #         rich.print(f"Adding new address {new_ip} {new_name}")
    #         cmd = f'sudo su -c \'echo "{new_ip} {new_name}"\' >> /etc/hosts'
    #         print(cmd)
    #         os.system(cmd)

    addresses = {a.split("=")[0]:a.split("=")[1] for a in infrastructure["addresses"]}
    rich.print(addresses)

    if hostname == services["proxy"]:
        rich.print("[cyan]=== Setting up NAT ===")
        # Check that all
        for mapping in infrastructure["port_mappings"]:
            try:
                protocol, src, hostname, dest = mapping.split(":")
            except ValueError:
                rich.print(f"[red]ERROR: wrong format in port_mapping '{mapping}'")

            ip_address = addresses[hostname]  # convert from hostname to IP

            # Run the command:
            cmd = f"sudo {args.script} {src} '{ip_address}' {dest} {protocol}"
            rich.print(f"Running command => {cmd}")
            os.system(cmd)
