#!/usr/bin/env python3
"""
This file includes utilities used acroos the project

author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 14/11/23
"""
import docker
import ipaddress
import traceback
import rich
import os
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
import time


def check_required_keys(conf: dict, required_keys: dict):
    """
    Checks that all keys in the 'keys' dict are present in 'conf' and ensures its data type
    :param conf: dict to check
    :param required_keys: dictionary with {<key_name>: <type>}, e.g. {"mandatoryKey": str}
    :raises: ValueError if error
    """
    for key in required_keys.keys():
        if key not in conf.keys():
            e = f"Required key '{key}' not found!"
            raise ValueError(e)
        elif type(conf[key]) == type(None):
            # allow empty types
            pass
        elif type(conf[key]) != required_keys[key]:
            e = f"Unexpected type for '{key}', expected {required_keys[key]} got {type(conf[key])}"
            raise ValueError(e)


def check_optional_keys(conf: dict, keys: dict):
    """
    Checks that the keys in the conf dict are compliant with the 'keys' dict.
    :param conf: dict to check
    :param keys: dictionary with {<key_name>: <type>}, e.g. {"mandatoryKey": str}
    :raises: ValueError if error
    """
    for key in conf.keys():
        if key not in keys:
            e = f"Unexpected key '{key}' found!"
            raise ValueError(e)
        elif type(conf[key]) != keys[key]:
            e = f"Unexpected type for '{key}', expected {keys[key]} got {type(conf[key])}"
            raise ValueError(e)


def split_command(cmd: str) -> list:
    """
    Splits a command into a list, taking into account literals, e.g.
    'psql -c "CREATE DB test;" --port 5432' -> ["psql", "-c", "CREATE DB test;", "--port", "5432"]
    """
    literal = False
    out = ""
    for i in range(len(cmd)):
        c = cmd[i]
        if c == '"' or c == "'":
            literal = not literal  # toggle literal
        elif literal and c == " ":
            out += "$#%"  # replace space by $#% to avoid collisions
        else:
            out += c
    slices = out.split(" ")
    return [s.replace("$#%", " ") for s in slices]  # convert back $#% to space


def run_subprocess(cmd: str, allow_fail=False, verbose=False, quiet=False):
    """
    Runs a command as a subprocess. If the process retunrs 0 returns True. Otherwise prints stderr and stdout and returns False
    :param cmd: command
    :return: True/False
    """
    assert (type(cmd) is str)
    cmd_list = split_command(cmd)
    if verbose:
        rich.print(f"[purple]{cmd}")
    proc = subprocess.run(cmd_list, capture_output=True)
    if proc.returncode != 0:
        if not quiet:
            rich.print(f"\n[red]ERROR while running command '{cmd}'")
            if proc.stdout:
                rich.print(f"subprocess stdout:")
                rich.print(f">[bright_black]    {proc.stdout.decode()}")
            if proc.stderr:
                rich.print(f"subprocess stderr:")
                rich.print(f">[bright_black] {proc.stderr.decode()}")
        if not allow_fail:
            raise ValueError("subprocess failed, exit")
        return False
    return True


def run_subprocess_pipe(command: list | str, allow_fail=False, debug=False):
    assert isinstance(command, str) or isinstance(command, list), f"expected list or str, got {type(command)}"

    # if isinstance(command, str):
    #     command = command.split(" ")

    if isinstance(command, list):
        command = " ".join(command)

    if debug:
        rich.print(f"Running command [purple]'{command}'")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    # Read and print the output in real-time
    while True:
        output = process.stdout.readline()
        err = process.stderr.readline()
        if output == '' and err == '' and process.poll() is not None:
            break
        if output:
            rich.print(f"[grey42]>  {output.strip()}")
        if err:
            rich.print(f"[grey42]>  {err.strip()}")
    retcode = process.poll()
    if retcode != 0:
        rich.print(f"[red]ERROR command '{command}' returned {retcode}")
        if not allow_fail:
            raise ValueError("subprocess failed, exit")


def setup_log(name, path, logger_name="logº"):
    level = logging.INFO
    if not os.path.exists(path):
        os.makedirs(path)

    filename = os.path.join(path, name)
    if not filename.endswith(".log"):
        filename += ".log"
    print("Creating log", filename)
    print("name", name)

    logger = logging.getLogger()
    logger.setLevel(level)
    log_formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)-7s: %(message)s',
                                      datefmt='%Y/%m/%d %H:%M:%S')
    handler = TimedRotatingFileHandler(filename, when="midnight", interval=1, backupCount=7)
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(log_formatter)
    logger.addHandler(consoleHandler)
    logger.info("")
    logger.info(f"===== {logger_name} =====")
    return logger


def container_stop(name):
    """
    Stops a container by name
    """
    client = docker.DockerClient()
    container = client.containers.get(name)
    container.stop()


def container_start(name):
    """
    Starts a container by name
    """
    client = docker.DockerClient()
    container = client.containers.get(name)
    container.start()


def container_exec(name, cmd) -> (int, bytes):
    """
    Runs a docker exec command
    """
    client = docker.DockerClient()
    container = client.containers.get(name)
    exit_code, output = container.exec_run(cmd)
    return exit_code, output


def container_get_ip(name, docker_network=""):
    # find the IP from a docker container
    client = docker.DockerClient()
    container = client.containers.get(name)
    ip_address = container.attrs["NetworkSettings"]["Networks"][docker_network]["IPAddress"]
    return ip_address




