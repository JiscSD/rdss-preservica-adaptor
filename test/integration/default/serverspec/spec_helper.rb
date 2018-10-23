require 'serverspec'
require 'net/ssh'

set :backend, :ssh

if ENV['ASK_SUDO_PASSWORD']
  begin
    require 'highline/import'
  rescue LoadError
    fail "highline is not available. Try installing it."
  end
  set :sudo_password, ask("Enter sudo password: ") { |q| q.echo = false }
else
  set :sudo_password, ENV['SUDO_PASSWORD']
end

host = ENV['TARGET_HOST']
key = ENV['SSH_KEY']
user = ENV['SSH_USER']

options = Net::SSH::Config.for(host)

options[:user] = user if user
options[:keys] = [key] if key

set :host,        options[:host_name] || host
set :ssh_options, options
