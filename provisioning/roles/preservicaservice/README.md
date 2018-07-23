preservicasercice
=================

Manages preservica service including:
- packages installation
- virtual environment
- application configuration
- logging


Requirements
------------

Basic requirements: python2

Role Variables
--------------

    # packages required + extra
    preservicaservice_packages:
     - python3.5-dev
     - python3.5-venv
     - python3.5
     - git
     - build-essential
     - libffi-dev
     - libssl-dev
     - libxml2-dev
     - rsyslog
     - openjdk-8-jdk-headless
     # extra packages for debug
     - curl
     - htop
     - iftop
     - iotop
     - openssh-client
     - openssh-server
     - rsync
     - strace
     - sudo
     - tmux
     - unzip
     - vim
     - wget
    # which user to run service under, defines install path as well
    preservicaservice_username: preservicaservice
    # syslog facility
    preservicaservice_syslog_facility: local0
    # file to redirect syslog
    preservicaservice_syslog_folder: /var/log/preservicaservice
    preservicaservice_syslog_file: '{{preservicaservice_syslog_folder}}/debug.log'
    # installation folder
    preservicaservice_install_path: '/home/{{preservicaservice_username}}/app'


Dependencies
------------

    - role: Oefenweb.locales
    locales_present:
      - en_US.UTF-8
    locales_default:
      lang: en_US.UTF-8
    - role: adriagalin.timezone
    ag_timezone: Etc/UTC
    - Oefenweb.ntp


Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: preservicaservice, preservicaservice_username: www-data }

License
-------

Propriate

Author Information
------------------

