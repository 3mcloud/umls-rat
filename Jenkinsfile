pipeline {
    triggers {
        cron(env.BRANCH_NAME == 'main' ? 'H H * * 1' : '')
    }
    options {
        buildDiscarder(logRotator(numToKeepStr: '12'))
        timeout(time: 60, unit: 'MINUTES')
    }
    agent {
        kubernetes {
            cloud "aws-pr-eks"
            yamlFile 'jenkins/build.yaml'
            activeDeadlineSeconds 2400
            slaveConnectTimeout 2400
        }
    }

    environment {
        OWNERS        = "rklopfer@mmm.com"
        ARTIFACTORY_PYTHON_REGISTRY = 'internal-python'
        ARTIFACTORY_URL = 'https://artifactory-pit.mmodal-npd.com/artifactory'
    }

    stages {

        stage("Setup"){
            steps{
                rtServer (
                    id: "ARTIFACTORY_SERVER",
                    url: "${ARTIFACTORY_URL}",
                    credentialsId: "mmodal_builder_artifactory_creds"
                )
            }
        }

        stage('Test Versions') {
            parallel {
                stage('3.7') {
                    stages {
                        stage ('Install Requirements') {
                            steps {
                                container(name: '37-tester'){
                                    sh 'pip3 install -r jenkins/requirements.txt'
                                }
                            }
                        }
                        stage ('Test') {
                            steps {
                                container(name: '37-tester'){
                                    withCredentials([string(credentialsId: 'rklopfer_umls_api_key', 
                                                            variable: 'UMLS_API_KEY')]) {
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 37-unittests.xml tests/'
                                        // running again should use cached requests, be super speedy, and also still work
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 37-unittests-cached.xml tests/'
                                        // make sure this script works
                                        sh 'python definitions-dump.py --source-desc="Wild Animal" --language=SPA'
                                    }
                                }
                            }
                            post {
                                always {
                                    junit testResults: '37-unittests*.xml'
                                }
                            }
                        }
                    }
                }

                stage('3.8') {
                    stages {
                        stage ('Install Requirements') {
                            steps {
                                container(name: '38-tester'){
                                    sh 'pip3 install -r jenkins/requirements.txt'
                                }
                            }
                        }
                        stage ('Test') {
                            steps {
                                container(name: '38-tester'){
                                    withCredentials([string(credentialsId: 'rklopfer_umls_api_key', 
                                                            variable: 'UMLS_API_KEY')]) {
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 38-unittests.xml tests/'
                                        // running again should use cached requests, be super speedy, and also still work
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 38-unittests-cached.xml tests/'
                                        // make sure this script works
                                        sh 'python definitions-dump.py --source-desc="Wild Animal" --language=SPA'
                                    }
                                }
                            }
                            post {
                                always {
                                    junit testResults: '38-unittests*.xml'
                                }
                            }
                        }
                    }
                }

                stage('3.9') {
                    stages {
                        stage ('Install Requirements') {
                            steps {
                                container(name: '39-tester'){
                                    sh 'pip3 install -r jenkins/requirements.txt'
                                }
                            }
                        }
                        stage ('Test') {
                            steps {
                                container(name: '39-tester'){
                                    withCredentials([string(credentialsId: 'rklopfer_umls_api_key', 
                                                            variable: 'UMLS_API_KEY')]) {
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 39-unittests.xml tests/'
                                        // running again should use cached requests, be super speedy, and also still work
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 39-unittests-cached.xml tests/'
                                        // make sure this script works
                                        sh 'python definitions-dump.py --source-desc="Wild Animal" --language=SPA'
                                    }
                                }
                            }
                            post {
                                always {
                                    junit testResults: '39-unittests*.xml'
                                }
                            }
                        }
                    }
                }

                stage('3.10') {
                    stages {
                        stage ('Install Requirements') {
                            steps {
                                container(name: '310-tester'){
                                    sh 'pip3 install -r jenkins/requirements.txt'
                                }
                            }
                        }
                        stage ('Test') {
                            steps {
                                container(name: '310-tester'){
                                    withCredentials([string(credentialsId: 'rklopfer_umls_api_key', 
                                                            variable: 'UMLS_API_KEY')]) {
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 310-unittests.xml tests/'
                                        // running again should use cached requests, be super speedy, and also still work
                                        sh 'python -m pytest -p no:cacheprovider -v --junitxml 310-unittests-cached.xml tests/'
                                        // make sure this script works
                                        sh 'python definitions-dump.py --source-desc="Wild Animal" --language=SPA'
                                    }
                                }
                            }
                            post {
                                always {
                                    junit testResults: '310-unittests*.xml'
                                }
                            }
                        }
                    }
                }
            }
        }

        stage ('Documentation') {
            steps {
                container(name: '39-tester'){
                    withCredentials([string(credentialsId: 'rklopfer_umls_api_key', 
                                            variable: 'UMLS_API_KEY')]) {
                        sh 'pip install -r jenkins/doc-requirements.txt'
                        sh 'make -C docs clean html'
                    }
                }
            }
            post {
                success {
                    publishHTML (target: [
                                  allowMissing: false,
                                  alwaysLinkToLastBuild: true,
                                  keepAll: true,
                                  reportDir: 'docs/_build/html/',
                                  reportFiles: 'index.html',
                                  reportName: "Documentation"
                                ])
                }
            }
        }

        stage('Publish') {
            stages {
                stage('Pypi Version'){
                    stages {
                        stage('Tag'){
                            when { buildingTag() }
                            steps{
                                script{
                                    PYPI_VERSION = "${BRANCH_NAME}"
                                }
                            }
                        }
                        stage('Branch'){
                            when { not { buildingTag()} }
                            stages{
                                stage('Main'){
                                    when { branch 'main' }
                                    steps{
                                        script{
                                            PYPI_VERSION = "0.0.0.dev${BUILD_NUMBER}+${BRANCH_NAME}"
                                        }
                                    }
                                }
                                stage('Other'){
                                    when { not { branch 'main'} }
                                    steps{
                                        script{
                                            PYPI_VERSION = "0.0.0.dev0+${BRANCH_NAME}"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                stage('Build'){
                    steps{
                        container('39-tester') {
                            sh 'python3 -m pip install build'
                            sh "PYPI_VERSION=${PYPI_VERSION} python3 -m build"
                        }
                    }
                    post {
                        success {
                            archiveArtifacts artifacts: 'dist/*.whl', fingerprint: true
                            archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
                        }
                    }
                }
                stage('Deploy'){
                    steps{
                        //https://github.com/jfrog/project-examples/blob/master/jenkins-examples/pipeline-examples/declarative-examples/pip-examples/pip-example/Jenkinsfile
                        rtUpload (
                            serverId: "ARTIFACTORY_SERVER",
                            spec: """{
                                "files": [
                                    {
                                        "pattern": "dist/",
                                        "target": "${ARTIFACTORY_PYTHON_REGISTRY}/",
                                        "props": "pypi.summary=umls-rat;pypi.name=umls-rat;pypi.version=${PYPI_VERSION};pypi.normalized.name=umls-rat"
                                    }
                                ]
                            }"""
                        )
                    }
                }
                stage("Build Information"){
                    steps {
                        rtPublishBuildInfo (
                        serverId: "ARTIFACTORY_SERVER"
                        )
                    }
                }
            }
        }
        
    }

    post {
        always {
            maybeSendEmail(this)
        }
    }

}
