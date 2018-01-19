# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/xenial64"
  # config.vm.provision "ansible_local" do |ansible|
  #   ansible.playbook = "setup.yml"
  #   ansible.provisioning_path = "./provisioning"
  # end

  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get -y upgrade
    sudo locale-gen en_GB.UTF-8
  SHELL
end
