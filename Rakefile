require 'rake'
require 'rspec/core/rake_task'

task :spec    => 'spec:all'
task :default => :spec

namespace :spec do
  task :all     => [:suite]
  task :default => :all

  RSpec::Core::RakeTask.new(:suite) do |t|
    t.pattern = "test/integration/default/serverspec/**/*_spec.rb"
  end
end
