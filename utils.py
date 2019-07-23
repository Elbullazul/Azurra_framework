#!/usr/bin/python3

# Azurra Utils, a management script to create, edit and manage Azurra-based themes
# Author: Christian Medel <cmedelahumada@gmail.com>
# This was

import argparse, os, sys

# Program constants
from typing import Any
import os.path

VERSION = 0.1
ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))


# Console colors
class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():
    if sys.version_info[0] != 3 and sys.version_info[1] < 7:
        print(colors.FAIL + 'This script requires Python 3.7 or newer' + colors.ENDC)
        exit(1)

    parser = argparse.ArgumentParser(description="Azurra Utils, a management script for the Azurra framework")
    ops = parser.add_mutually_exclusive_group()
    optargs = parser.add_mutually_exclusive_group()

    # operational arguments
    ops.add_argument("-p", "--parents", type=str, help='Shows external dependencies for <TARGET> theme')
    ops.add_argument("-c", "--children", type=str, help='Shows shows themes depending on <TARGET> theme')
    ops.add_argument("-n", "--new", type=str, help='Initiates new resource <NEW>')

    # optional arguments
    optargs.add_argument("-w", "--widget", type=str, help='Filter dependencies to <WIDGET>')
    optargs.add_argument("-b", "--base", type=str, default='Azurra',
                         help='Which resource the new resource should be base on (theme only)')
    parser.add_argument("-u", "--bundle", action='store_true', help='Signals to create a new bundle instead of theme')
    parser.add_argument("-i", "--ignore-base", action='store_true', help='Ignore entries for base theme (Azurra)')

    # pretty args
    parser.add_argument("-v", "--version", action='version', version='Azurra Utils, version 1.0 alpha',
                        help='Shows script version and exists')
    args = parser.parse_args()

    if args.parents:
        parents(args.parents, args.widget, args.ignore_base)

    elif args.children:
        children(args.children, args.widget)

    elif args.new:
        new(args.new, args.base, args.bundle)


def read_file(target: str):
    try:
        with open(f"{target}/_imports.scss", "r") as file:
            imports = file.readlines()

        return imports
    except FileNotFoundError:
        print(colors.FAIL + f"Target '{target}' does not have a valid import file" + colors.ENDC)
        exit(2)


def contains_filters(line: str, filters):
    for filter in filters:
        if filter in line:
            return True
    return False


def not_in(line: str, filters):
    for filter in filters:
        if filter not in line:
            return True
    return False


def read_parents(target: str, filters: Any, ignore_base: bool):
    count = 0
    total = 0
    imports = []
    lines = read_file(target)

    for line in lines:
        if "'widgets/" not in line:
            line = line.rstrip()
            if not (ignore_base and 'Azurra' in line):
                if None not in filters:
                    if not not_in(line, filters):
                        imports += [clean_string(line)]
                        count += 1
                else:
                    imports += [clean_string(line)]
                    count += 1

        total += 1

    return [imports, count, total]


def parents(target: str, widget: Any, ignore_base: bool):
    print(colors.OKBLUE + f"Getting parents for '{target}'" + colors.ENDC)

    returned = read_parents(target, [widget], ignore_base)
    imports = returned[0]
    count = returned[1]
    total = returned[2]

    for line in imports:
        print(line)

    if count > 0:
        print(colors.OKGREEN + f"Found {count} children imports over {total} imports" + colors.ENDC)
    else:
        print(colors.FAIL + f"Found {count} children imports over {total} imports" + colors.ENDC)


def clean_string(input: str) -> str:
    string = input.strip("@import '")
    string = string.strip('../')
    string = string.strip("';")
    string = f" - {string}"

    return string


def get_children(target, source, widget):
    if widget is None:
        filters = [source]
    else:
        filters = [source, widget]

    returned = read_parents(target, filters, False)

    imports = returned[0]
    count = returned[1]

#    if count > 0:
#        print(f"Parents for {target}")

    for line in imports:
        target = target.split('/')[-1]
        print(line.replace(source, f'[{target}]').replace('/', '').replace('widgets', ' '))

    return count


def get_subdirs(source: str):
    return sorted([name for name in os.listdir(source) if
            os.path.isdir(os.path.join(source, name)) and not name.startswith('.')])


def children(target: str, widget: Any):
    print(f"Children for {target}")
    count = 0
    children = 0

    dirs = get_subdirs(ROOT_DIRECTORY)
    for dir in dirs:
        if os.path.isfile(f"{ROOT_DIRECTORY}/{dir}/theme.conf"):
            child_count = get_children(dir, target, widget)
            if child_count > 0:
                count += child_count
                children += 1

        for subdir in get_subdirs(f"{ROOT_DIRECTORY}/{dir}"):
            if os.path.isfile(f"{ROOT_DIRECTORY}/{dir}/bundle.conf"):
                child_count = get_children(f"{dir}/{subdir}", target, widget)
                if child_count > 0:
                    count += child_count
                    children += 1

    if count > 0:
        print(colors.OKBLUE + f"Found {count} parents over {children} themes" + colors.ENDC)
    else:
        print(colors.FAIL + f"Found {count} parents over {children} themes" + colors.ENDC)


def new(target: str, source: str, bundle: bool):
    print(f"Creating new resource '{target}' based on '{source}'")

    if bundle:
        print("Initializing new bundle")


if __name__ == "__main__": main()
