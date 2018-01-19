# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "setup.yml"
    ansible.provisioning_path = "./provisioning"
  end
end
