pipeline {
    agent {
        kubernetes {
            inheritFrom 'kaniko'
            yaml '''
              apiVersion: v1
              kind: Pod
              spec:
                serviceAccountName: previews-deployer
                containers:
                  - name: kubectl
                    image: alpine/k8s:1.36.2
                    command: ["sleep"]
                    args: ["9999999"]
            '''
        }
    }
    environment {
        IMAGE_NAME = 'blog'
        REGISTRY   = '192.168.1.20:5000'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git submodule update --init --recursive'
            }
        }
        stage('Build & Push') {
            steps {
                container('kaniko') {
                    script {
                        def buildDrafts = (env.BRANCH_NAME == 'drafts') ? 'true' : 'false'
                        sh """
                        /kaniko/executor \
                          --context="\$(pwd)" \
                          --dockerfile=Dockerfile \
                          --build-arg BUILD_DRAFTS=${buildDrafts} \
                          --destination=${REGISTRY}/${IMAGE_NAME}:${env.BRANCH_NAME}-${env.BUILD_NUMBER} \
                          --insecure --skip-tls-verify
                        """
                    }
                }
            }
        }
        stage('Deploy preview') {
            when { branch 'drafts' }
            steps {
                container('kubectl') {
                    sh """
                    sed 's|IMAGE_TAG_PLACEHOLDER|${env.BRANCH_NAME}-${env.BUILD_NUMBER}|' deploy/preview.yaml | kubectl apply -f -
                    kubectl -n previews rollout status deployment/blog-preview --timeout=120s
                    """
                }
            }
        }
    }
}
