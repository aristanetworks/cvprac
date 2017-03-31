#!/usr/bin/env groovy

/**
 * Jenkinsfile
 */

projectName = 'CvpRac'
emailTo = 'jere@arista.com'
emailFrom = 'eosplus-dev+jenkins@arista.com'

node('exec') {

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
                // Stub dummy .cloudvision.yaml file
                writeFile file: "test/fixtures/cvp_nodes.yaml", text: "---\n- node: 10.81.111.10\n  username: cvpadmin\n  password: cvp123\n- node: 10.81.111.11\n  username: cvpadmin\n  password: cvp123\n- node: 10.81.111.12\n  username: cvpadmin\n  password: cvp123\n"
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
                    make pep8 | tee pep8_report.txt
                    make pyflakes
                    make pylint | tee pylint.out || true
                """
                step([$class: 'WarningsPublisher',
                  parserConfigurations: [[
                    parserName: 'Pep8',
                    pattern: 'pep8_report.txt'
                  ],
                  [
                    parserName: 'pylint',
                    pattern: 'pylint.out'
                  ]],
                  unstableTotalAll: '0',
                  usePreviousBuildAsReference: true
                ])
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
                    make coverage_report
                    coverage xml
                """

                step([$class: 'JUnitResultArchiver', testResults: 'coverage.xml'])
                // publish html
                /*
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: false,
                    keepAll: true,
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'])
                */

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
