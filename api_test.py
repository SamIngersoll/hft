#! /usr/bin/env python3

import toml

cfg = toml.load("configuration.toml")

auth_cfg = cfg["auth"]
api_cfg = cfg["api"]
