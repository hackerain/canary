# Canary

[![Build Status](https://travis-ci.org/hackerain/canary.svg?branch=master)](https://travis-ci.org/hackerain/canary)

Canary is an ansible project collecting some common operational tasks.

## Usage

1. Get the code:

    ```
    git clone https://github.com/hackerain/canary.git
    ```

2. Install dependencies

    ```
    ./start.sh --install-deps
    ```

3. Define your inventory

    You should define your inventory according your environments. Modify the
    inventory/hosts file.

4. Define your configuration

    Edit the config.yml to fit your environments.

5. Run your code, for example:

    ```
    ./start.sh -p playbooks/setup_network.yml  # setup node network using os-net-config
    ```
6. To get more help info

    ```
    ./start.sh -h
    ```
