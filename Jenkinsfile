#!groovy

pipeline {
    agent none

    parameters {
        string(
            defaultValue: 'master',
            description: 'Git branch to use in job',
            name: 'GIT_BRANCH'
        )

        choice(
            choices: 'dev\nuat\ntest\nprod',
            description: 'Environment to deploy to',
            name: 'ENVIRONMENT'
        )
    }

    environment {
        REGION = 'eu-west-2'
        ACCOUNT_ID = '458323522494'
        DEPLOY_VAR_FILE = "deploy_build_vars.json"
    }

    stages {
        stage('fetch code') {
            agent any
            steps {
                deleteDir()
                git(
                    credentialsId: 'git',
                    url: 'git@github.com:JiscRDSS/rdss-preservica-adaptor.git',
                    branch: params.GIT_BRANCH
                )
            }
        }

        stage('test') {
            agent { dockerfile true }
            steps {
                sh 'make lint test'
                junit 'junit.xml'
            }
        }

        stage('packer') {
            agent { dockerfile true }
            steps {
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY_ID', credentialsId: 'jenkins_aws', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],
                ]) {
                    sh "bin/buildami"
                    stash(name: "deploy_build_vars", includes: 'deploy_build_vars.json')
                }
            }
        }

        stage('deploy') {
            agent { dockerfile true }
            steps {
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY_ID', credentialsId: 'jenkins_aws', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],
                ]) {
                    unstash "deploy_build_vars"
                    sh "bin/deployterraform"
                }
            }
        }
    }
}
