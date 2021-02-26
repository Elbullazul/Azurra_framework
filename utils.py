#!/usr/bin/python3

import os, argparse

BUNDLE_FILENAME = "bundle.conf"
IMPORTS_FILENAME = "_imports.scss"
THEME_CONFIG_FILENAME = "theme.conf"

EMPTY = ""
UPPER_DIR_INDICATOR = "../"

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

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

def read_file(filename: str):
    try:
        with open(filename, "r") as file:
            imports = file.read().splitlines()

        return imports
    except FileNotFoundError:
        print(colors.FAIL + f"File '{filename}' doesn't exist" + colors.ENDC)
        exit(2)

### Format methods
def clean(line: str):
    line = line.strip("@import '")
    line = line.strip("';")

    return line

def is_empty(value):
    if value == "" or value == None:
        return True
    else:
        return False

def split(line: str):
    line = line.strip(UPPER_DIR_INDICATOR)

    return [line.split('/widgets/')[0], line.split('/widgets/')[1]]

def filter_theme(pack_theme, theme: str):
    # Remove trailing slash before, it causes issues
    if theme.endswith("/"):
        theme = theme[:-1]
    
    if not is_empty(theme):
        if pack_theme == theme:
            return True
        else:            
            if "/" in theme:
                return filter_theme(pack_theme, theme.split("/")[1])
            else:
                return False
    else:
        return True

def filter_widget(pack_widget, widget: str):
    if not is_empty(widget):
        if pack_widget == widget:
            return True
        else:
            return False
    else:
        return True

### Logic methods
def parents(theme: str, parent: str, widget: str, skip_widgets: bool):
    resultset = get_parents(theme, parent, widget)
    parents = resultset[0]
    parent_count = len(resultset[1])

    # For theme-only list    
    previous = ''
    
    for item in parents:
        if skip_widgets and item[0] != previous:
            print(f"- {item[0]}")
            previous = item[0]
        elif not skip_widgets:
            print(f"{item[0]}/widgets/{item[1]}")   # parent theme and widget
    
    if skip_widgets:
        print(f"Found {parent_count} parents for theme {theme}")
    else:
        print(f"Found {len(parents)} results over {parent_count} external dependencies")

def get_parents(theme: str, parent: str, widget: str):
    imports = get_external_imports(theme)
    parent_list = []
    ret = []

    for pack in imports:
        if filter_theme(pack[0], parent) and filter_widget(pack[1], widget):
            ret += [pack]

            if pack[0] not in parent_list:
                parent_list.append(pack[0])
    
    return [ret, parent_list]

def get_external_imports(theme: str):
    external_imports = []
    imports = read_file(f"{theme}/{IMPORTS_FILENAME}")

    for line in imports:
        line = clean(line)

        if is_external_resource(line):
            external_imports += [split(line)]
    
    return external_imports

def get_internal_imports(theme: str):
    internal_imports = []
    imports = read_file(f"{theme}/{IMPORTS_FILENAME}")

    for line in imports:
        line = clean(line)

        if not is_external_resource(line):
            internal_imports += [line.replace("widgets/", EMPTY)]
    
    return internal_imports

def is_external_resource(line: str):
    return line.startswith(UPPER_DIR_INDICATOR)

def children(theme: str, widget: str, skip_widgets: bool):
    resultset = []
    children = []
    child_count = 0

    resultset = get_children(theme, widget)
    children = resultset[0]
    child_count = len(resultset[1])
    
    # For theme-only list
    previous = ''
    
    for item in children:
        if skip_widgets and item[0] != previous:
            print(f"- {item[0]}")
            previous = item[0]
        elif not skip_widgets:
            print(f"[{item[0]}] {item[1]}")   # parent theme and widget
    
    if skip_widgets:
        print(f"Found {child_count} children for theme {theme}")
    else:
        print(f"Found {len(children)} results over {child_count} children")

def get_children(theme: str, widget: str):
    resultset = []
    children = []
    child_list = []

    resultset = get_imports_recursive(EMPTY, subdirs(CURRENT_DIRECTORY))

    themes = resultset[0]
    imports = resultset[1]

    for idx in range(len(themes)):
        for pack in imports[idx]:
            if filter_theme(pack[0], theme) and filter_widget(pack[1], widget):
                children.append([themes[idx], pack[1]])

                if themes[idx] not in child_list:
                    child_list.append(themes[idx])
    
    return [children, child_list]

def get_imports_recursive(prefix: str, folders):
    # prefix is the parent folder name + /, if it's not the base folder
    themes = []
    imports = []
    sub_results = []

    for DIR in folders:
        DIR_PATH = f"{prefix}{DIR}"

        if is_theme(DIR_PATH):
            themes += [DIR]
            imports += [get_external_imports(DIR_PATH)]

        if is_bundle(DIR_PATH):
            sub_results = get_imports_recursive(f"{DIR_PATH}/", subdirs(DIR_PATH))

            themes.extend(sub_results[0])
            imports.extend(sub_results[1])

    return [themes, imports]

def is_bundle(folder: str):
    return os.path.isfile(f"{CURRENT_DIRECTORY}/{folder}/{BUNDLE_FILENAME}")

def is_theme(folder: str):
    return os.path.isfile(f"{CURRENT_DIRECTORY}/{folder}/{THEME_CONFIG_FILENAME}")

def subdirs(source: str):
    return sorted([name for name in os.listdir(source) if
            os.path.isdir(os.path.join(source, name)) and not name.startswith('.')])

def implementations(theme: str):
    imports = get_internal_imports(theme)

    print(f"Implemented widgets for {theme}")

    for item in imports:
        print(f"- {item}")   # parent theme and widget
    
    print(f"Found {len(imports)} results")

def conflicts(theme: str):
    parents = get_parents(theme, EMPTY, EMPTY)[1]
    children = get_children(theme, EMPTY)[1]

    for theme in parents:
        for child in children:
            if filter_theme(child, theme) or filter_theme(theme, child):
                print(f"CRITICAL: {theme} is also a child!")
                return
    
    print("No cross-dependencies found")

# parents(TEST_THEME, TEST_PARENT, TEST_WIDGET)
# children(TEST_THEME, TEST_WIDGET)
# implementations(TEST_THEME)
# conflicts(TEST_THEME)

TEST_THEME = "Win_XP/luna"
TEST_PARENT = "Azurra"
TEST_WIDGET = ""

def main():

    parser = argparse.ArgumentParser(description="Azurra Utils, a management script for the Azurra framework")
    ops = parser.add_mutually_exclusive_group()
    optargs = parser.add_mutually_exclusive_group()

    # operational arguments
    ops.add_argument("-p", "--parents", type=str, help='Shows external dependencies for <TARGET> theme')
    ops.add_argument("-c", "--children", type=str, help='Shows themes depending on <TARGET> theme')
    ops.add_argument("-i", "--implementations", type=str, help='Shows unique widgets for <TARGET>')
    ops.add_argument("-x", "--conflicts", type=str, help='Detect if theme is cross-dependent on any child')

    # optional arguments
    optargs.add_argument("-w", "--widget", type=str, help='Filter results to match <WIDGET>')
    optargs.add_argument("-l", "--list", help='Show only theme names, skipping widgets', action='store_true')

    # pretty args
    parser.add_argument("-v", "--version", action='version', version='Azurra Utils, version 1.0',
                        help='Shows script version and exists')
    args = parser.parse_args()
    
    if args.parents:
        parents(args.parents, EMPTY, args.widget, args.list)

    elif args.children:
        children(args.children, args.widget, args.list)

    elif args.implementations:
        implementations(args.implementations)
    
    elif args.conflicts:
        conflicts(args.conflicts)

if __name__ == "__main__": main()
