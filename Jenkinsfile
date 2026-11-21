// Pipeline CI/CD - SecureDev
// Etapas: Build -> Dependency Management -> Test -> Analyze -> Deploy -> Security Test
// Cubre: construcción, pruebas y despliegue (mínimo exigido) + revisiones de
// seguridad continuas en cada etapa, gestión de dependencias y pruebas
// automatizadas de seguridad con OWASP ZAP.

pipeline {
    agent any

    environment {
        IMAGE_NAME     = 'flask-app-securedev'
        TEST_CONTAINER = 'flask-app-securedev-test'
        APP_PORT       = '5000'
    }

    stages {

        stage('Build') {
            steps {
                echo '=== BUILD: construyendo la imagen Docker de la aplicación ==='
                sh 'docker build -t ${IMAGE_NAME}:latest .'
            }
        }

        stage('Dependency Management') {
            steps {
                echo '=== DEPENDENCY MANAGEMENT: instalando y auditando dependencias ==='
                sh 'pip install --user pipenv pip-audit || true'
                sh 'pipenv install -r requirements.txt'
                sh 'pipenv update'
                sh 'pipenv graph | tee pipenv-graph.txt'
                // No se detiene el pipeline si pip-audit encuentra algo: se deja
                // evidencia en el log/archivo para la etapa de documentación.
                sh 'pipenv run pip-audit -r requirements.txt | tee pip-audit-report.txt || true'
            }
        }

        stage('Test') {
            steps {
                echo '=== TEST: pruebas unitarias y de seguridad (pytest) ==='
                sh 'pipenv run pytest tests.py -v'
            }
        }

        stage('Analyze') {
            steps {
                echo '=== ANALYZE: análisis estático de seguridad del código (Bandit) ==='
                sh 'pipenv run pip install bandit || true'
                sh 'pipenv run bandit -r app.py -f txt | tee bandit-report.txt || true'
            }
        }

        stage('Deploy') {
            steps {
                echo '=== DEPLOY: desplegando la aplicación en el entorno de prueba ==='
                sh 'docker rm -f ${TEST_CONTAINER} || true'
                sh 'docker run -d --name ${TEST_CONTAINER} -p ${APP_PORT}:5000 ${IMAGE_NAME}:latest'
                sh 'sleep 5'
                sh 'curl -sf "http://localhost:${APP_PORT}/hello?name=Jenkins"'
            }
        }

        stage('Security Test') {
            steps {
                echo '=== SECURITY TEST: escaneo dinámico con OWASP ZAP (baseline scan) ==='
                sh '''
                    docker run --rm -v "$(pwd):/zap/wrk/:rw" -t zaproxy/zap-stable zap-baseline.py \
                        -t "http://host.docker.internal:${APP_PORT}/hello?name=ZAPscan" \
                        -r zap-report.html || true
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline finalizado. Evidencia de seguridad generada: zap-report.html, bandit-report.txt, pip-audit-report.txt, pipenv-graph.txt'
            archiveArtifacts artifacts: 'zap-report.html, bandit-report.txt, pip-audit-report.txt, pipenv-graph.txt', allowEmptyArchive: true
        }
    }
}
