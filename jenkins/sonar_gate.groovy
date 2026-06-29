def branch() {
    return {
        stage('SonarQube Scan') {
            node('klymene') {
                deleteDir()
                unstash 'source'
                def checks = load 'jenkins/checks.groovy'
                def execution = load 'jenkins/execution.groovy'
                [
                    'report-pytest-coverage',
                    'report-ruff-lint',
                    'report-ruff-format',
                    'report-mypy',
                    'report-translations',
                    'report-pip-audit',
                    'report-gitleaks',
                    'report-trivy',
                    'report-codeql'
                ].each { execution.unstashOptional(it) }

                checks.run('SonarQube Scan') { logFile ->
                    execution.loggedShell(
                        "mkdir -p ${env.SB_NAME}/sonar && find ${env.SB_NAME}/sonar -type f | sort || true",
                        logFile
                    )
                    withSonarQubeEnv('SonarQube') {
                        withCredentials([string(credentialsId: 'Sonarqube', variable: 'SONAR_TOKEN')]) {
                            execution.inCi("""
                                SONAR_BIN="\$(command -v sonar-scanner || true)"
                                if [ -z "\$SONAR_BIN" ] && command -v pysonar >/dev/null 2>&1; then
                                    SONAR_BIN="\$(command -v pysonar)"
                                fi
                                if [ -z "\$SONAR_BIN" ]; then
                                    echo "Neither sonar-scanner nor pysonar is available in the CI image."
                                    exit 1
                                fi
                                SONAR_ARGS="-Dsonar.host.url=https://sonarqube.home.siczb.de -Dsonar.token=\${SONAR_TOKEN} -Dsonar.projectKey=teltonika_rms -Dsonar.projectName=teltonika_rms -Dsonar.projectVersion=${env.VERSION}-${env.COMMIT_HASH} -Dsonar.python.version=3.14 -Dsonar.sources=custom_components/teltonika_rms -Dsonar.tests=tests"
                                if [ -f "${env.SB_NAME}/sonar/tests/coverage.xml" ]; then
                                    SONAR_ARGS="\$SONAR_ARGS -Dsonar.python.coverage.reportPaths=${env.SB_NAME}/sonar/tests/coverage.xml"
                                fi
                                if [ -f "${env.SB_NAME}/sonar/tests/pytest.xml" ]; then
                                    SONAR_ARGS="\$SONAR_ARGS -Dsonar.python.xunit.reportPath=${env.SB_NAME}/sonar/tests/pytest.xml"
                                fi
                                "\$SONAR_BIN" \$SONAR_ARGS
                            """, '--env SONAR_TOKEN', logFile)
                        }
                    }
                }
            }
        }
    }
}

return this
