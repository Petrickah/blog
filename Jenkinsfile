pipeline {
    // Docker-CI migration (Homelab Redux Valul 1): Kaniko/K8s retired along
    // with the K3s cluster. Jenkins now runs as a Docker container on the
    // same host as the registry, with /var/run/docker.sock mounted, so
    // image builds go through the host's own Docker daemon directly.
    //
    // "Deploy preview" stage removed (not ported): it did `kubectl apply`
    // into K3s's `previews` namespace, which no longer exists. The preview
    // feature is intentionally offline until a Docker-based replacement is
    // designed (Valul 2/3) — see Homelab Redux project note.
    agent { label 'built-in' }
    environment {
        IMAGE_NAME = 'blog'
        REGISTRY   = '192.168.1.21:5000'
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
                script {
                    def buildDrafts = (env.BRANCH_NAME == 'drafts') ? 'true' : 'false'
                    def tag = "${REGISTRY}/${IMAGE_NAME}:${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
                    sh """
                    docker build --build-arg BUILD_DRAFTS=${buildDrafts} -t ${tag} .
                    docker push ${tag}
                    """
                }
            }
        }
    }
}
