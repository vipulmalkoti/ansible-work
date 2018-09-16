release-automation
==================

# Ansible playbooks

Create your own password file:
```
$ ansible-vault create kerberos_pass.yml
ansible_sudo_pass: ...
stage_ud_pass: ...
prod_ud_pass: ...
```

Where ansible_sudo_pass is your kerberos password that will be used for sudo on rcm-dev. You will be asked for vault passord - that will be used to encode/hide private passwords you add there.

Notes:
ansible+ssh doesn't support 'sudo' on RHEL6 (rcm-dev)
ansible+paramiko doesn't support kerberos ticket login -> use SSH key based auth

Test that everything works as expected:
$ ansible-playbook test.yml -u $USER

AEP Beta release
$ ansible-playbook aep-beta-stage.yml -u $USER --extra-vars "var_advisory=NNNNN var_ose_pulp=3_DOT_1"

OSE Clients release
$ ansible-playbook ose-clients-stage-before-sign.yml -u $USER --extra-vars "var_clients_version=3.1.?.? var_ose_pulp=3_DOT_1 var_ose_human=3.1 var_rpm_path=/mnt/redhat/brewroot/packages/..."
$ ansible-playbook ose-clients-stage-after-sign.yml -u $USER --extra-vars "var_clients_version=3.1.?.? var_ose_pulp=3_DOT_1 var_ose_human=3.1 var_rpm_path=/mnt/redhat/brewroot/packages/..."

RM OSE Clients release
$ ansible-playbook rm-ose-clients-stage.yml -u $USER --extra-vars "var_clients_version=3.1.?.? var_ose_pulp=3_DOT_1 var_ose_human=3.1"

Release Clients to Openshift Online
$ ansible-playbook oso-clients-upload.yml -u $USER --extra-vars "var_clients_version=3.1.?.? var_ose_pulp=3_DOT_1 var_ose_human=3.1"

Upload productid
$ ansible-playbook product-id-stage.yml -u $USER --extra-vars "var_pulp_label=PULP_LABEL var_productid=product_ids/..."

# Various

Parse yaml file and prints 'pub push-docker' commands:
$ python parse-docker-input.py --target=cdn-docker-stage --inputfile=somefile.yml
(optinonally you can add --ignoreerrors)

