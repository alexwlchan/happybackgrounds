#!/usr/bin/env bash

set -o errexit
set -o nounset

python3 happybackgrounds.py \
    --background="#d6fcff" \
    --icon_name="snowflake" \
    --out_path="snowflake.svg"

python3 happybackgrounds.py \
    --background="#000314" \
    --icon_name="star" \
    --out_path="starfield.svg" \
    --min_scale=0.2 \
    --max_scale=0.6

python3 happybackgrounds.py \
    --background="#c24400" \
    --icon_name="rocket" \
    --out_path="mars.svg" \
    --min_scale=0.2 \
    --max_scale=0.6

python3 happybackgrounds.py \
    --background="#a7ff99" \
    --icon_name="seedling" \
    --out_path="plants.svg" \
    --min_icon_count=35 \
    --max_icon_count=40 \
    --min_scale=0.1 \
    --max_scale=0.25

python3 happybackgrounds.py \
    --background="#ffc905" \
    --icon_name="grin-beam" \
    --out_path="happy.svg"
