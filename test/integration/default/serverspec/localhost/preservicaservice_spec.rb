require 'serverspec'
require 'spec_helper'

describe package('python3.5') do
  it { should be_installed }
end

describe package('rsyslog') do
  it { should be_installed }
end

describe package('openjdk-8-jdk-headless') do
  it { should be_installed }
end

describe user('preservicaservice') do
  it { should exist }
  it { should belong_to_group 'preservicaservice' }
end

describe file('/home/preservicaservice/app/.env.provisioning/bin/preservicaservice') do
  it { should be_file }
  it { should be_mode 755 }
end

describe file('/home/preservicaservice/app/.env.provisioning/bin/amazon_kclpy_helper.py') do
  it { should be_file }
  it { should be_mode 755 }
end

describe file('/home/preservicaservice/app/bin/run') do
  it { should be_file }
  it { should be_mode 755 }
end

describe file('/lib/systemd/system/preservicaservice.service') do
  it { should be_file }
end

describe file('/var/log/preservicaservice') do
  it { should be_directory }
  it { should be_owned_by 'syslog' }
end

describe file('/etc/rsyslog.d/70-preservicaservice.conf') do
  it { should be_file }
  it { should contain 'local0.*  /var/log/preservicaservice/debug.log' }
end

describe file('/etc/logrotate.d/preservicaservice') do
  it { should be_file }
  it { should contain '/var/log/preservicaservice/debug.log' }
end
