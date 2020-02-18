# Ansible playbook to deploy PyGrid components (for Debian based systems)

## Install ansible

Before you try run any ansible script, you need install ansible. You can find more
information about installation to your linux distribution [here](http://docs.ansible.com/ansible/intro_installation.html).

If you use Debian based distribution, you can install using the commands below:

```
$ apt-get update
$ apt-get install ansible
```

### Editing ansible.cfg to not ask ssh key host checking

SSH always ask if you sure in establish a ssh connection in your first time that you try to connect in a machine. For jump this, ucomment the line in **/etc/ansible/ansible.cfg**:

```
host_key_checking = False
```

## Add keys in machine that will be managed

To ansibe install and configure machine, it is necessary that your key is added in
**.ssh/authorized_keys** in machine that will be managed. To do this, run the command
below:

```
$ ssh-copy-id -i ~/<route_ssh_public_key> <user>@<ip_or_hostname>
```

## Add hosts to the inventory

Before all, add the hosts that will recieve the containers to inventory file like:

```
[hosts]
0.0.0.0 #host1
127.0.0.1 #host2
```

## Run the playbook

Run the playbook using the command below:

```
$ ansible-playbook -i inventory pygrid_deploy.yaml
```

#### WARNING:
PyGrid nodes require PyGrid gateway and Redis service to be up and running, so deploy them first (always put their tasks before in the playbook)

