#!/bin/bash

# Azurra string_ops v 0.1
# Run string modification ops on all theme folders
# WARNING: use with caution!

# PROGRAM VARS
OP=''         # call appropriate string op when iterating on folders
VAL=''        # used in search, append and replace ops
NEW_VAL=''    # used in replace ops

# HELP
ops() {
  echo "Available options:"
  echo "  -fc    --find-in-colors       <VALUE>"
  echo "  -fw    --find-in-widgets      <VALUE>"
  echo "  -rg    --replace-in-gtk-files <VALUE> <NEW_VALUE>"
  echo "  -ri    --replace-in-imports   <VALUE> <NEW_VALUE>"
  echo "  -rw    --replace-in-widgets   <VALUE> <NEW_VALUE>"
  echo "  -ac    --append-to-conf-file  <VALUE>"
}

help() {
  echo "Azurra string ops v0.1"
  echo "Run string modification ops on all theme folders"
  echo ""
  
  ops
}

# UTILS
# $1: target  $2: new value  $3: filename
replace() {
  sed -i "s@$1@$2@g" "$3"
}

# $1: target  $2: filename
file_contains() {
  result=$(grep "$1" "$2")
  
  # 0 is OK, 1 is error
  [[ ! -z $result ]] && return 0 || return 1  
}

# iterate on all theme folders
run() {
  for dir in *; do
    if [ -f "$dir/theme.conf" ]  # if has valid configuration
    then
      $OP "$dir" "$VAL" "$NEW_VAL"
    elif [ -f "$dir/bundle.conf" ]  # if is a bundle directory
    then
      for bundle_dir in "$dir"/*
      do
        if [ -f "$bundle_dir/theme.conf" ]  # process bundled themes
        then
          $OP "$bundle_dir" "$VAL" "$NEW_VAL"
        fi    
      done
    fi
  done
}

# OPERATIONS
colors_contains() {
  local theme_dir="$1"
  local value="$2"
  
  if file_contains "$value" "$theme_dir/_colors.scss"; then
    echo "Match in folder $theme_dir"
  fi
}

widgets_contains() {
  local theme_dir="$1"
  local value="$2"
  local hits=0

  for FILE in "$theme_dir/widgets/"*; do
    if [ ! -f "$FILE" ]; then continue; fi
    
    if file_contains "$value" "$FILE"; then
      echo "Match in file $FILE"
      hits=$((hits+1))
    fi
  done
  
  [ $hits -le 0 ] && echo "No matches found"
}

gtk_replace() {
  local theme_dir="$1"
  local value="$2"
  local new_value="$3"
  
  # replace in gtk*.scss files
  [ -f "$theme_dir/gtk.scss" ] && replace "$value" "$new_value" "$theme_dir/gtk.scss"
  [ -f "$theme_dir/gtk-light.scss" ] && replace "$value" "$new_value" "$theme_dir/gtk-light.scss"
  [ -f "$theme_dir/gtk-dark.scss" ] && replace "$value" "$new_value" "$theme_dir/gtk-dark.scss"
  
  echo "Replaced value in gtk*.scss files (if found)"
}

imports_replace() {
  local theme_dir="$1"
  local value="$2"
  local new_value="$3"
  
  replace "$value" "$new_value" "$theme_dir/_imports.scss"
  
  echo "Replaced value in '$theme_dir/_imports.scss' (if found)"
}

widgets_replace() {
  local theme_dir="$1"
  local value="$2"
  local new_value="$3"
  
  # replace 'value' by 'new_value'
  for FILE in "$theme_dir"/widgets/*.scss; do
    [ -f $FILE ] && replace "$value" "$new_value" $FILE && echo "Replacing value in $FILE (if found)"
  done
}

config_append() {
  local theme_dir="$1"
  local string="$2"
  
  echo "$string" >> "$theme_dir/theme.conf"
}

OP="$!"
VAL="$2"
NEW_VAL="$3"

case $1 in
  -fc|--find-in-colors)
    OP="colors_contains"
  ;;
  -fw|--find-in-widgets)
    OP="widgets_contains"
  ;;
  -rg|--replace-in-gtk-files)
    OP="gtk_replace"
  ;;
  -ri|--replace-in-imports)
    OP="imports_replace"
  ;;
  -rw|--replace-in-widgets)
    OP="widgets_replace"
  ;;
  -ac|--append-to-conf-file)
    OP="config_append"
  ;;
  *)
    echo -n "Invalid operation. "
    ops
    exit 1
  ;;
esac

# warn user of potential catastrophic consequences
read -p "Files will be altered. Continue? (y/n): " -n 1 -r
echo ""	# new line

if [[ $REPLY =~ ^[Yy]$ ]]
then
  run
else
  echo "Operation aborted."
fi
