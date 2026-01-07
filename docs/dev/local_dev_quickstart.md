# Local Dev Environment Quickstart Guide

This repo is intended to quickly get a developer started with a local Golden Config instance using sample data, virtual Arista lab devices, and a local ephemeral Git server.

By default, this guide will automatically deploy 2 Arista virtual cEOS devices and 1 Git server as Docker containers, then fully configure Nautobot and Golden Config with all required objects for 4 devices named "ceos[1-4]". Finally, it will run the inital Golden Config Job for backups, intended, and compliance against all 4 devices.

The number of devices can be specified when running the management command in step 6 below using the `--device-count` option.

> Note: If creating more than 4 virtual devices, you will need to

- Add new containers to development/docker-compose.arista.dev.yml
- Create startup configs in `development/startup_configs/` to add additional devices and their corresponding IP addresses

Follow these steps to quickly get a new dev instance spun up for Nautobot's [Golden Config App](https://github.com/nautobot/nautobot-app-golden-config).

## Prerequisites

This setup currently supports only Arista cEOS devices. Before starting, you will need to download the corresponding cEOS image for your CPU architecture from the Arista [software download site](https://www.arista.com/en/support/software-download). You will need a free Arista account to access the download.

Once logged in, download the latest cEOS Lab image for your architecture:

- x64 / Apple Intel: `cEOS64-lab-4.34.2F.tar.xz`
- ARM / Apple Silicon: `cEOSarm-lab-4.34.2F.tar.xz`

Once downloaded, you will need to import the image into Docker as shown in step 1 below.

## Modifying Device Count (optional)

### Docker Compose File

If you want to modify the default number of devices (4) to another count, you will need to update the `development/docker-compose.arista.dev.yml` file to add/remove containers as needed.

All devices need to follow this format, substituting `#` with the device number:

```yaml
  ceos#:  # e.g. ceos1, ceos2, etc.
    <<: *ceos-common
    container_name: "ceos#"  # e.g. ceos1, ceos2, etc.
    hostname: "ceos#"  # e.g. ceos1, ceos2, etc.
    volumes:
      - "./startup_configs/ceos#/startup-config:/mnt/flash/startup-config"  # e.g. ceos1, ceos2, etc.
```

Additionally, you will need to create corresponding startup configs in `development/startup_configs/ceos#/startup-config`. Use the `startup-config-template` as a base config. Only the hostname needs to be updated. All other parameters should remain the same to ensure connectivity.

Replace `#` with the device number below:

```bash
    mkdir -p development/startup_configs/ceos# # e.g. ceos1, ceos2, etc.
    cp development/startup_configs/startup-config-template development/startup_configs/ceos#/startup-config
    nano development/startup_configs/ceos#/startup-config
    # Update hostname in the config file on line 2 to "ceos#" - e.g. ceos1, ceos2, etc.
```

## Setup Steps

1. Import the corresponding Arista image based on your CPU architecture.

    ```bash
    docker import cEOS64-lab-4.34.2F.tar.xz ceos:latest   # x64 image
    docker import cEOSarm-lab-4.34.2F.tar.xz ceos:latest  # ARM image
    ```

2. Build and import the Git server image, updating the existing `gclab` repo, or adding any new repos you want, before building the image (see development/gitserver_image/README.md for details).

    ```bash
    docker build -t git-server:latest development/gitserver_image
    ```

3. Clone the Golden Config app and set up Poetry.

    ```bash
    poetry build
    poetry install
    poetry env activate
    ```

4. In your Golden Config local dev folder, copy `invoke.example.yml` to `invoke.yml` and uncomment all configuration lines, including the settings for Docker Compose files `docker-compose.arista.dev.yml` and `docker-compose.git.dev.yml`. Lastly, change setting `compose_dir` to point to the `development/` folder.

5. Start the Nautobot Golden Config dev instance. Note: Wait for it and all 4 cEOS containers to fully boot up before proceeding.

    ```bash
    invoke build
    invoke start  # or invoke debug
    ```

6. Connect to the Nautobot container with `invoke cli` and run the management command `nautobot-server setup_local_dev_environment`. Specify the number of devices to create using the `--device-count` option. If not specified, it will default to 1 device.

    ```bash
    invoke cli
    $ nautobot-server setup_local_dev_environment --device-count=2
    ```

7. Login to [http://localhost:8080](http://localhost:8080) using the default admin/admin credentials.

8. Navigate to `Jobs --> Jobs` and Run the Golden Config Job `Execute All Golden Configuration Jobs - Multiple Device`. Do not specify any parameters, as it will run against all configured devices.

## Optional

### Startup Configs

Modify the startup configs used by each `ceos` device in `development/startup_configs/ceos#/startup-config`

### Clone Local Repos

Once the Git server is up and running alongside Nautobot and Golden Config, you can clone any repo from it that was added into the build via `git clone http://localhost:3000/gclab`, or for a new folder/repo added, `git clone http://localhost:3000/<folder-name>`.

No authentication is required.

## Run Git Server Locally

To run the Git server container locally without incorporating it into Golden Config, build and run the image as follows:

```bash
docker build -t git-server:latest image/
docker compose up -d
```
