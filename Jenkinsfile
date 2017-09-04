#!groovy
pipeline {
  agent none
  parameters {
    choice(
      choices: 'dev\nuat\nprod',
      description: 'Environment to deploy to',
      name: 'ENVIRONMENT'
    )
  }
  environment {
    REGION = 'eu-west-2'
    ACCOUNT_ID = '458323522494'
    DEPLOY_VAR_FILE = "deploy_build_vars.json"
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '100'))
  }
  stages {
    stage('fetch code') {
      agent any
      steps {
        deleteDir()
        git(
          credentialsId: 'git',
          url: 'git@github.com:JiscRDSS/rdss-preservica-adaptor.git',
          branch: "${BRANCH_NAME}"
        )
      }
    }
    stage('packer') {
      agent { dockerfile true }
      steps {
        ansiColor('xterm') {
          withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY_ID', credentialsId: 'jenkins_aws', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],]) {
            sh "bin/buildami"
            stash(name: "deploy_build_vars", includes: 'deploy_build_vars.json')
          }
        }
      }
    }
    stage('deploy') {
      agent { dockerfile true }
      steps {
        ansiColor('xterm') {
          withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY_ID', credentialsId: 'jenkins_aws', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],]) {
            unstash "deploy_build_vars"
            sh "mkdir -p  ~/.ssh/ && ssh-keyscan github.com | tee -a ~/.ssh/known_hosts"
            sshagent(['git']) {
              sh "bin/deployterraform"
            }
          }
        }
      }
    }
  }
}
