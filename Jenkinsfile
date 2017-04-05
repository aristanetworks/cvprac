#!/usr/bin/env groovy

/**
 * Jenkinsfile
 */
pipeline {
    agent{ label 'exec'}
    options {
        buildDiscarder(
            // Only keep the 10 most recent builds
            logRotator(numToKeepStr:'10'))
    }
    environment {
        projectName = 'CvpRac'
        emailTo = 'eosplus-dev@arista.com'
        emailFrom = 'eosplus-dev+jenkins@arista.com'
    }

    stages {

        stage ('Checkout') {
            steps {
                checkout scm
            }
        }

        stage ('Install_Requirements') {
            steps {
                sh """
                    [[ -d venv ]] && rm -rf venv
                    virtualenv --python=python2.7 venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r dev-requirements.txt
                    pip install codecov
                """
                // Stub dummy .cloudvision.yaml file
                writeFile file: "test/fixtures/cvp_nodes.yaml", text: "---\n- node: 10.81.111.9\n  username: cvpadmin\n  password: cvp123\n"
            }
        }

        stage ('Check_style') {
            steps {
                sh """
                    source venv/bin/activate
                    make clean
                    [[ -d report ]] || mkdir report
                    echo "exclude report" >> MANIFEST.in
                    echo "exclude htmlcov" >> MANIFEST.in
                    make check || true
                    make pep8 | tee report/pep8_report.txt
                    make pyflakes
                    make pylint | tee report/pylint.out || true
                """
                step([$class: 'WarningsPublisher',
                  parserConfigurations: [[
                    parserName: 'Pep8',
                    pattern: 'report/pep8_report.txt'
                  ],
                  [
                    parserName: 'pylint',
                    pattern: 'report/pylint.out'
                  ]],
                  unstableTotalAll: '0',
                  usePreviousBuildAsReference: true
                ])
            }
        }

        stage ('System Test') {
            steps {
                sh """
                    source venv/bin/activate
                    #make tests || true
                    nosetests --with-xunit --all-modules --traverse-namespace --with-coverage --cover-package=cvprac --cover-inclusive --cover-html test/system/* || true
                """
            }

            post {
                always {
                    junit keepLongStdio: true, testResults: 'nosetests.xml'
                    publishHTML target: [
                        reportDir: 'cover',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ]
                }
            }
        }

        stage ('Docs') {
            steps {
                sh """
                    source venv/bin/activate
                    PYTHONPATH=. pdoc --html --html-dir docs --overwrite cvprac
                """
            }

            post {
                always {
                    publishHTML target: [
                        reportDir: 'docs/cvprac',
                        reportFiles: 'index.html',
                        reportName: 'Module Documentation'
                    ]
                }
            }
        }

        stage ('Cleanup') {
            steps {
                sh 'rm -rf venv'
            }
        }
    }

    post {
        failure {
            mail body: "${env.JOB_NAME} (${env.BUILD_NUMBER}) ${env.projectName} build error " +
                       "is here: ${env.BUILD_URL}\nStarted by ${env.BUILD_CAUSE}" ,
                 from: env.emailFrom,
                 //replyTo: env.emailFrom,
                 subject: "${env.projectName} ${env.JOB_NAME} (${env.BUILD_NUMBER}) build failed",
                 to: env.emailTo
        }
        success {
            mail body: "${env.JOB_NAME} (${env.BUILD_NUMBER}) ${env.projectName} build successful\n" +
                       "Started by ${env.BUILD_CAUSE}",
                 from: env.emailFrom,
                 //replyTo: env.emailFrom,
                 subject: "${env.projectName} ${env.JOB_NAME} (${env.BUILD_NUMBER}) build successful",
                 to: env.emailTo
        }
    }
}
