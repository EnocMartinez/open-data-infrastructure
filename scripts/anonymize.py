#!/usr/bin/env python3
"""
Anonymize secrets.env file to allow its publication on github

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 5/11/23
"""

from argparse import ArgumentParser
import os
import rich
import random
import string
import secrets
from datetime import datetime


def generate_password(pass_length=-1):
    valid_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    if pass_length < 4:
        pass_length = random.randint(50, 70)
    password = ""
    while pass_length > 0:
        password += secrets.choice(valid_chars)
        pass_length -= 1
    return password


default_values = {
    "EMAIL_SMPT_USER": "my.email.user@gmail.com",
    "EMAIL_SMPT_FROM_ADDRESS": "my.email.user@gmail.com",
    "EMAIL_SMPT_PASSWORD": "MyEmailPassword"
}

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("-i", "--input", help="Path no secrets.env", type=str, default="/opt/odi/secrets.env")
    argparser.add_argument("-o", "--output", help="Output no secrets.env", type=str,
                           default="/opt/odi/secrets.env.template")
    argparser.add_argument("-a", "--only-one", help="Generate only one password no secrets.env", action="store_true")
    args = argparser.parse_args()

    if args.only_one:
        print(generate_password())
        exit()

    rich.print(f"Anonymizing file {args.input} to {args.output}")
    f1 = open(args.input)
    f2 = open(args.output, "w")

    f2.write(f"# secrets file anonymized by ODI at " + datetime.now().strftime("%Y-%m-%d at %H:%M:%S"))
    f2.write("\n")

    for line in f1.readlines():
        line = line.strip()
        key = line.split("=")[0]
        # First, check the default values
        if key in default_values.keys():
            rich.print(f"    setting default {key}...")
            line = f"{key}={default_values[key]}"

        # If we don't have a default value and we have a password, generate it
        elif "PASSWORD" in line:
            rich.print(f"    anonymizing {key}...")
            old_password = line.split("=")[1]

            if old_password.startswith("string:"):
                # Make sure to create a string with the same length as the old one
                password = "string:" + generate_password(pass_length=int(len(old_password) - len("string:")))
            else:
                password = generate_password()
            line = f"{key}={password}"

        f2.write(line + "\n")
    rich.print("[green]done!")
    f1.close()
    f2.close()
