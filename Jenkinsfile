#!/usr/bin/env groovy

/**
 * Jenkinsfile
 */

projectName = 'CvpRac'
emailTo = 'jere@arista.com'
emailFrom = 'eosplus-dev+jenkins@arista.com'

node() {

    currentBuild.result = "SUCCESS"

    try {

        stage ('Checkout') {
            checkout scm
            def tag = sh(script: 'git describe --tags --match \"v[0-9]*\" --abbrev=7 --always', returnStdout: true)
            echo ">>> Tag: ${tag} <<<"
        }

        stage ('Install_Requirements') {
            try {
                sh """
                    virtualenv --python=python2.7 venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r dev-requirements.txt
                    pip install codecov
                """
            }
            catch (Exception err) {
                throw err
            }
            echo "Install Requirements RESULT: ${currentBuild.result}"
        }

        stage ('Check_style') {
            try {
                sh """
                    source venv/bin/activate
                    make clean
                    make check
                    make pep8
                    make pyflakes
                    make pylint || true
                """
            }
            catch (Exception err) {
                currentBuild.result = "UNSTABLE"
            }
            echo "Check Style RESULT: ${currentBuild.result}"
        }

        stage ('System Test') {
            try {
                sh """
                    source venv/bin/activate
                    make tests
                """

                // publish html
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: false,
                    keepAll: true,
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'])

            }
            catch (Exception err) {
                currentBuild.result = "UNSTABLE"
            }
            echo "System Test RESULT: ${currentBuild.result}"
        }

        stage ('Cleanup') {
            try {
                sh 'rm -rf venv'
            }
            catch (Exception err) {
                currentBuild.result = "UNSTABLE"
            }
            echo "Cleanup RESULT: ${currentBuild.result}"
        }
    }

    catch (err) {
        currentBuild.result = "FAILURE"

            mail body: "${env.JOB_NAME} (${env.BUILD_NUMBER}) ${projectName} build error " +
                       "is here: ${env.BUILD_URL}\nStarted by ${env.BUILD_CAUSE}" ,
                 from: emailFrom,
                 replyTo: emailFrom,
                 subject: "${projectName} ${env.JOB_NAME} (${env.BUILD_NUMBER}) build failed",
                 to: emailTo

            throw err
    }
}
