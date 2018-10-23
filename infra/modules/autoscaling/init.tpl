#!/bin/bash

echo ENVIRONMENT=${environment} >> ${env_file_path}

curl https://s3.amazonaws.com//aws-cloudwatch/downloads/latest/awslogs-agent-setup.py -O
chmod +x ./awslogs-agent-setup.py
./awslogs-agent-setup.py -n -r eu-west-2 -c s3://rdss-preservicaservice-objects/application/config/${environment}/node/awslogs-agent-config.conf

until $(ping -c 1 ietf.org >/dev/null 2>&1); do sleep 1; done
systemctl reset-failed
systemctl restart ${systemd_unit}
