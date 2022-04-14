pipeline {
    triggers {
        cron(env.BRANCH_NAME == 'main' ? 'H H * * *' : '')
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

        stage ('Install Requirements') {
            steps {
                container(name: 'target'){
                    sh 'python3 -m venv --system-site-packages venv'
                    sh 'venv/bin/pip3 install -r jenkins/requirements.txt'
                }
            }
        }

        stage ('Test') {
            steps {
                container(name: 'target'){
                    withCredentials([string(credentialsId: 'rklopfer_umls_api_key', 
                                            variable: 'API_KEY')]) {
                        sh 'venv/bin/python -m pytest -v --junitxml unittests.xml tests/ --api-key=${API_KEY}'
                        // running again should use the cache, be super speedy, and also still work
                        sh 'venv/bin/python -m pytest -v --junitxml unittests-cached.xml tests/ --api-key=${API_KEY}'
                    }
                }
            }
            post {
                always {
                    junit testResults: 'unittests*.xml'
                }
            }
        }

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
                container('target') {
                    sh 'venv/bin/python3 -m pip install build'
                    sh "PYPI_VERSION=${PYPI_VERSION} venv/bin/python3 -m build"
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

    post {
        always {
            maybeSendEmail(this)
        }
    }

}
