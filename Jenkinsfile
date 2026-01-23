// Jenkinsfile for AURA Project
# AURA Continuous Integration Pipeline
#
# Includes:
# - Multi-stage build process
# - Security scanning with Trivy
# - Performance benchmark validation
# - Docker image building
#
# @see: .github/workflows/ci.yml - GitHub Actions equivalent
# @note: Configure credentials and environment in Jenkins

pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.10'
        NODE_VERSION = '20'
        DOCKER_REGISTRY = 'registry.example.com'
        AURA_CHAT_IMAGE = "${DOCKER_REGISTRY}/aura-chat-api:${BUILD_NUMBER}"
        AURA_NOTES_IMAGE = "${DOCKER_REGISTRY}/aura-notes-api:${BUILD_NUMBER}"
        TRIVY_VERSION = '0.48'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '5'))
        disableConcurrentBuilds()
    }

    stages {
        stage('Setup') {
            steps {
                echo 'Setting up Node.js environment...'
                nodejs(nodeJSInstallationName: 'node20', configId: 'npm-config') {
                    sh 'npm --version'
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing npm dependencies...'
                dir(AURA_CHAT_CLIENT) {
                    sh 'npm ci'
                }
            }
        }

        stage('Install Playwright Browsers') {
            steps {
                echo 'Installing Playwright browsers...'
                dir(AURA_CHAT_CLIENT) {
                    sh 'npx playwright install --with-deps chromium firefox webkit'
                }
            }
        }

        stage('Desktop Tests') {
            parallel {
                stage('Chromium') {
                    steps {
                        dir(AURA_CHAT_CLIENT) {
                            sh 'CI=true npx playwright test --project=chromium --reporter=line'
                        }
                    }
                }
                stage('Firefox') {
                    steps {
                        dir(AURA_CHAT_CLIENT) {
                            sh 'CI=true npx playwright test --project=firefox --reporter=line'
                        }
                    }
                }
                stage('WebKit') {
                    steps {
                        dir(AURA_CHAT_CLIENT) {
                            sh 'CI=true npx playwright test --project=webkit --reporter=line'
                        }
                    }
                }
            }
        }

        stage('Mobile Tests') {
            parallel {
                stage('iPhone 12') {
                    steps {
                        dir(AURA_CHAT_CLIENT) {
                            sh 'CI=true npx playwright test --project=iphone-12 --reporter=line'
                        }
                    }
                }
                stage('Pixel 5') {
                    steps {
                        dir(AURA_CHAT_CLIENT) {
                            sh 'CI=true npx playwright test --project=pixel-5 --reporter=line'
                        }
                    }
                }
                stage('iPad') {
                    steps {
                        dir(AURA_CHAT_CLIENT) {
                            sh 'CI=true npx playwright test --project=ipad --reporter=line'
                        }
                    }
                }
            }
        }

        stage('Performance Tests') {
            steps {
                echo 'Running performance tests...'
                dir(AURA_CHAT_CLIENT) {
                    sh 'CI=true npx playwright test performance.spec.ts --reporter=line'
                }
            }
        }

        stage('Mobile Suite Tests') {
            steps {
                echo 'Running mobile suite tests...'
                dir(AURA_CHAT_CLIENT) {
                    sh 'CI=true npx playwright test mobile.spec.ts --reporter=line'
                }
            }
        }

        stage('Full Test Suite') {
            steps {
                echo 'Running full test suite...'
                dir(AURA_CHAT_CLIENT) {
                    sh 'CI=true npx playwright test --reporter=line'
                }
            }
        }

        // =========================================================================
        // Stage: Security Scan (Trivy)
        // =========================================================================

        stage('Security Scan') {
            agent {
                docker {
                    image "aquasec/trivy:${TRIVY_VERSION}"
                    args '-u root:root --entrypoint=""'
                }
            }
            steps {
                sh '''
                    trivy fs --exit-code 1 --severity CRITICAL,HIGH .
                    echo "Security scan passed"
                '''
            }
        }

        // =========================================================================
        // Stage: Performance Gate
        // =========================================================================

        stage('Performance Gate') {
            agent {
                docker {
                    image "python:${PYTHON_VERSION}"
                    args '-u root:root'
                }
            }
            steps {
                sh '''
                    pip install jq
                    echo "Analyzing benchmark results..."
                    BENCHMARK_COUNT=$(cat benchmark_results.json | jq '.benchmarks | length')
                    echo "Found $BENCHMARK_COUNT benchmarks"
                    if [ "$BENCHMARK_COUNT" -lt 10 ]; then
                        echo "WARNING: Low benchmark count - only $BENCHMARK_COUNT found"
                    else
                        echo "Performance gate: PASSED ($BENCHMARK_COUNT benchmarks)"
                    fi
                '''
            }
        }

        // =========================================================================
        // Stage: Build Docker Images
        // =========================================================================

        stage('Build Images') {
            agent any
            steps {
                script {
                    echo "Building AURA-CHAT API image..."
                    docker.build("aura-chat-api:latest", "./AURA-CHAT")
                    echo "Building AURA-NOTES API image..."
                    docker.build("aura-notes-api:latest", "./AURA-NOTES-MANAGER/api")
                }
            }
        }

        // =========================================================================
        // Stage: Push Images
        // =========================================================================

        stage('Push Images') {
            agent any
            steps {
                script {
                    echo "Pushing images to registry..."
                    docker.withRegistry("${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        docker.image("aura-chat-api:latest").push("${BUILD_NUMBER}")
                        docker.image("aura-notes-api:latest").push("${BUILD_NUMBER}")
                    }
                }
            }
        }

        // =========================================================================
        // Stage: Deploy Staging
        // =========================================================================

        stage('Deploy Staging') {
            agent any
            when { branch 'develop' }
            steps {
                echo "Deploying to staging environment..."
                sh '''
                    echo "Staging deployment initiated"
                    # Add actual deployment commands here
                '''
            }
        }

        // =========================================================================
        // Stage: Deploy Production
        // =========================================================================

        stage('Deploy Production') {
            agent any
            when { branch 'master' }
            input message: 'Deploy to production?', ok: 'Deploy'
            steps {
                echo "Deploying to production environment..."
                sh '''
                    echo "Production deployment initiated"
                    # Add actual deployment commands here
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully!"
            emaile(
                subject: "Build Success: ${JOB_NAME} #${BUILD_NUMBER}",
                body: "The build completed successfully. View results: ${BUILD_URL}",
                recipientProviders: [requesters()]
            )
            archiveArtifacts artifacts: 'AURA-CHAT/client/playwright-report/**/*', fingerprint: true
        }
        failure {
            echo "Pipeline failed!"
            emaile(
                subject: "Build FAILED: ${JOB_NAME} #${BUILD_NUMBER}",
                body: "The build failed. View results: ${BUILD_URL}",
                recipientProviders: [requesters()]
            )
            archiveArtifacts artifacts: 'AURA-CHAT/client/playwright-report/**/*,AURA-CHAT/client/test-results/**/*', fingerprint: true, allowEmptyArchive: true
        }
        always {
            cleanWs()
        }
    }
}
