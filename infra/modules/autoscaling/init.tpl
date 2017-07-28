#!/bin/bash

echo ENVIRONMENT=${environment} >> ${env_file_path}

until $(ping -c 1 ietf.org >/dev/null 2>&1); do sleep 1; done
systemctl reset-failed
systemctl restart ${systemd_unit}
