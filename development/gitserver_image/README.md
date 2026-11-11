# Git-Server

This will build an image of a local Git server that runs on HTTP port 3000 with no authentication. It is used for quickly setting up a lab/dev environment for Golden Config or other Nautobot apps.

This image is intended for use with the GitHub repo https://github.com/networktocode-llc/gc-dev-setup.git

It comes with one existing repository installed with three folders:

* backups/
* intended/
* templates/

## Folders

### Backups

Folder is empty, but available to sync into from Golden Config.

### Intended

Folder is empty, but available to sync into from Golden Config.

### Templates

Contains a single Jinja2 template: `arista_eos.j2`

```jinja2
no aaa root
!
username lab privilege 15 secret labpass
!
!
hostname {{ hostname }}
dns domain networktocode.com
!
snmp-server contact John Smith
snmp-server location NYC
snmp-server community labpass ro
snmp-server community labsecure rw
snmp-server host 10.1.1.1 version 2c lab
!
spanning-tree mode mstp
!
ntp server 10.1.1.1
ntp server 10.2.2.2 prefer
!
management ssh
   server-port 22
   no shutdown
!
end
```

## Creating the Image

To create the image, run the following commands:

```bash
docker build -t git-server:latest .
docker run --rm -d -p 3000:3000 --name git-server git-server:latest
```

You can clone the built-in repo with:

```bash
git clone http://localhost:3000/gclab
```

To modify the contents of the repo, or add your own, in the `repos/` folder before building the image.

### Add A Repo

To add another repo to the image when building, just create a new folder in the `repos/` folder. The repository name will be the name of the folder, and all contents of the folder will be in the initial commit in the image's repository.
