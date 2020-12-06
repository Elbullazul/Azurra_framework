#!/bin/bash

# A script to quickly generate a list, bundle or all indexed themes
# Author: Christian Medel <cmedelahumada@gmail.com>
# License: GPLv3

version=3.0
description="Azurra Autogen, version $version"
base_theme='Azurra'
ROOT_DIR="$PWD"

show_help() {
  echo -e "$description\n"
  echo -e "Generates and deploys CSS and asset files\n"

  echo -e "Usage:  ./autogen.sh <ARGUMENTS> <TARGETS>\n"

  echo "  -h   --help         " "Shows help"
  echo "  -v   --version      " "Script version"
  echo "  -q   --quiet        " "Silences ALL SASS warnings"
  echo "  -a   --all          " "Generates and deploys all themes with valid configuration"
  echo "  -d   --deploy       " "Deploys current files"
  echo "  -c   --compile      " "Run SASS compiler only (no deployment)"
  echo "  -r   --render       " "Run asset generation script if found"
  echo "  -e   --empty-assets " "Removes previously rendered assets. Run before rendering after changes"

  echo -e "\nMore information: <http://github.com/Elbullazul/Azurra_framework/wiki>" && exit
}

show_version() {
  echo $description
  echo "Copyright (c) 2019 The b00merang Group"
  echo "License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>" && exit
}

fail() { tput setaf 1 && echo 'ERROR: '$@ && exit 1; }
warn() { tput setaf 220 && echo 'WARNING: '$@ && tput sgr 0; }
hlight() { tput setaf 33 && echo $@ && tput sgr 0; }

is_theme() { [ -f "$1/theme.conf" ] && return 0 || return 1; }
is_bundle() { [ -f "$1/bundle.conf" ] && return 0 || return 1; }
load_conf() { source $1/*.conf; }
has_dark() { [ -z $target_dir_dark ] && return 1 || return 0; }
has_light() { [ -z $target_dir_light ] && return 1 || return 0; }
has_render() {
  [ -d "$1/assets-render" ] || [ -d "$1/assets-render-light" ] || [ -d "$1/assets-render-dark" ] && return 0
  return 1
}

recursive() {
  for dir in $@; do
    is_theme $dir && $FUNC "$dir" || is_bundle $dir && recursive "$dir"/*
  done
}

deploy() {
  load_conf $1
  [ -z "$target_dir" ] && warn "Empty target for $name, skipping deployment" && return

  echo -n "Deploying $(hlight -n $name), "

  # Stylesheets
  rm -rf "$target_dir"/*.css
  has_dark && rm -rf "$target_dir_dark"/*.css
  has_light && rm -rf "$target_dir_light"/*.css

  cp $1/gtk*.css "$target_dir"
  
  # Specific deploys
  for stylesheet in $1/*.css; do
    stylesheet=$(basename $stylesheet)
    case $stylesheet in
      *dark*) has_dark && cp $1/$stylesheet "$target_dir_dark/${stylesheet/'-dark'/''}" ;;
      *light*) has_light && cp $1/$stylesheet "$target_dir_light/${stylesheet/'-light'/''}" ;;
    esac
  done

  # Assets
  rm -rf "$target_dir/assets"
  has_dark && rm -rf "$target_dir_dark/assets"
  has_light && rm -rf "$target_dir_light/assets"

  cp -r $1/assets "$target_dir"
  if has_dark; then
    [ -d $1/assets-dark ] && cp -r $1/assets-dark "$target_dir_dark/assets" || cp -r $1/assets "$target_dir_dark"
  fi
  if has_light; then
    [ -d $1/assets-dark ] && cp -r $1/assets-light "$target_dir_light/assets" || cp -r $1/assets "$target_dir_light"
  fi

  echo 'done'
}

compile() {
  load_conf $1
  [ $LOCK_ADD == true ] && echo -n "Compiling $(hlight -n $name), " || echo "Compiling $(hlight $name)"

  for sass_file in $1/gtk*.scss; do
    local filename=${sass_file%".scss"}
    sass $sass_args $sass_file $filename.css

    [ $? -ne 0 ] && fail "SASS exited unexpectedly, aborting"
  done

  echo 'done'
}

render() {
  has_render $1 || warn "$1 has no asset generation module"
  ! has_render $1 && return

  # run
  [ -d "$1/assets-render" ] && (cd "$1/assets-render" && ./render-assets.sh && cd ..)
  [ -d "$1/assets-render-dark" ] && (cd "$1/assets-render-dark" && ./render-assets.sh && cd ..)
  [ -d "$1/assets-render-light" ] && (cd "$1/assets-render-light" && ./render-assets.sh && cd ..)

  # local deploy
  cp -R "$1/assets-render/assets/"* "$1/assets"
  [ -d "$1/assets-render-dark" ] && cp -R "$1/assets-render-dark/assets/"* "$1/assets-dark"
  [ -d "$1/assets-render-light" ] && cp -R "$1/assets-render-light/assets/"* "$1/assets-light"
}

empty_assets() {
  has_render $1 || warn "$1 has no asset generation module"
  ! has_render $1 && return

  # run
  [ -d "$1/assets-render" ] && rm -rf "$1/assets-render/assets/"*
  [ -d "$1/assets-render-dark" ] && rm -rf "$1/assets-render-dark/assets/"*
  [ -d "$1/assets-render-light" ] && rm -rf "$1/assets-render-light/assets/"*
}

make() {
  compile $1
  deploy $1

  echo
}

# Program vars
FUNC="make"
LOCK_ADD=false
sass_args="-C --sourcemap=none"

declare -a QUEUE

while [ "$1" != "" ]; do
  case $1 in
    -a | --all )            QUEUE=*/
                            LOCK_ADD=true
                            sass_args="$sass_args -q"
                            ;;
    -q | --quiet )          sass_args="$sass_args -q"
                            ;;
    -c | --compile )        FUNC='compile'
                            ;;
    -d | --deploy )         FUNC='deploy'
                            ;;
    -r | --render )         FUNC='render'
                            ;;
    -e | --empty-assets )   FUNC='empty_assets'
                            ;;
    -h | --help )           show_help
                            ;;
    -v | --version )        show_version
                            ;;
    *)                      [ $LOCK_ADD == false ] && QUEUE+=("$1")
                            ;;
  esac
  shift
done

[ ${#QUEUE[@]} -eq 0 ] && fail 'Missing target(s), aborting'
recursive "${QUEUE[@]}"   # iterate on eligible folders, calling function FUNC
