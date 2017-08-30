pipeline {
    agent any
    stages {
        stage('Clone source') {
            steps {
                git 'https://github.com/rero/reroils-app'
            }
        }
        stage('Build Docker Image') {
            steps {
                echo 'Building..'
                script {
                    app = docker.build('rero/reroils-app')
                }
            }
        }
        stage('Run Test') {
            steps {
                echo 'Testing..'
            }
        }
        stage('Push Docker image') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                    /*app.push("${env.BUILD_NUMBER}")*/
                        app.push("latest")
                    }
                }
            }
        }
        stage('Kubernetes delployement') {
            steps {
                echo 'Deploying....'
                withCredentials([string(credentialsId: 'KUBE_SERVER_URL', variable: 'KUBE_SERVER_URL'),
                                 file(credentialsId: 'KUBE_SERVER_AUTHORITY', variable: 'KUBE_SERVER_AUTHORITY'),
                                 file(credentialsId: 'KUBE_SERVER_USER_CERT', variable: 'KUBE_SERVER_USER_CERT'),
                                 file(credentialsId: 'KUBE_SERVER_USER_KEY', variable: 'KUBE_SERVER_USER_KEY'),
                ]) {
                    sh '''
                        set +x
                        kubectl config --kubeconfig=config-demo set-cluster dev --server=$KUBE_SERVER_URL --certificate-authority=$KUBE_SERVER_AUTHORITY
                        kubectl config --kubeconfig=config-demo set-context dev --cluster=dev --user=dev
                        kubectl config --kubeconfig=config-demo set-credentials dev --client-certificate=$KUBE_SERVER_USER_CERT --client-key=$KUBE_SERVER_USER_KEY
                        kubectl --kubeconfig=config-demo config use-context dev
                        kubectl --kubeconfig=config-demo get pods
                        kubectl --kubeconfig=config-demo apply -f kubernetes
                    '''
                }
            }
        }
        stage('Cleaning') {
            steps {
                echo 'Cleaning....'
            }
        }
    }
}
