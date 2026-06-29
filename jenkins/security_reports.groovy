def gitleaksBranch(def scmConfig) {
    return {
        stage('Gitleaks Report') {
            node('klymene') {
                try {
                    deleteDir()
                    checkout scmConfig
                    def checks = load 'jenkins/checks.groovy'
                    def execution = load 'jenkins/execution.groovy'
                    execution.reportStage('gitleaks') {
                        checks.run('Gitleaks Report') { logFile ->
                            execution.loggedShell("""
                                mkdir -p ${env.SB_NAME}/sonar/gitleaks
                                podman run --rm -v "\$PWD:/repo:z" -w /repo \
                                  docker.io/zricethezav/gitleaks:latest detect \
                                  --source=/repo --redact --verbose --report-format=json \
                                  --report-path=${env.SB_NAME}/sonar/gitleaks/gitleaks-report.json
                            """, logFile)
                        }
                    }
                } finally {
                    stash name: 'report-gitleaks', includes: "${env.SB_NAME}/sonar/gitleaks/**", allowEmpty: true
                    stash name: 'qa-failure-marker-gitleaks', includes: '.ci-failures/gitleaks.failed', allowEmpty: true
                    archiveArtifacts artifacts: "${env.SB_NAME}/sonar/gitleaks/**", allowEmptyArchive: true
                }
            }
        }
    }
}

def trivyBranch() {
    return {
        stage('Trivy FS Report') {
            node('klymene') {
                try {
                    deleteDir()
                    unstash 'source'
                    def checks = load 'jenkins/checks.groovy'
                    def execution = load 'jenkins/execution.groovy'
                    execution.reportStage('trivy') {
                        checks.run('Trivy FS Report') { logFile ->
                            execution.loggedShell("""
                                mkdir -p ${env.SB_NAME}/sonar/trivy
                                podman run --rm -v "\$PWD:/app:z" -w /app \
                                  docker.io/aquasec/trivy:latest fs . \
                                  --severity HIGH,CRITICAL --format json \
                                  --output ${env.SB_NAME}/sonar/trivy/trivy-report.json \
                                  --no-progress
                            """, logFile)
                        }
                    }
                } finally {
                    stash name: 'report-trivy', includes: "${env.SB_NAME}/sonar/trivy/**", allowEmpty: true
                    stash name: 'qa-failure-marker-trivy', includes: '.ci-failures/trivy.failed', allowEmpty: true
                    archiveArtifacts artifacts: "${env.SB_NAME}/sonar/trivy/**", allowEmptyArchive: true
                }
            }
        }
    }
}

def codeqlBranch(def scmConfig) {
    return {
        stage('CodeQL Report') {
            node('klymene') {
                try {
                    deleteDir()
                    checkout scmConfig
                    def checks = load 'jenkins/checks.groovy'
                    def execution = load 'jenkins/execution.groovy'
                    def external = load 'jenkins/external_results.groovy'
                    execution.reportStage('codeql') {
                        def codeqlHome = tool name: 'codeql'
                        withEnv(["CODEQL_HOME=${codeqlHome}", "PATH=${codeqlHome}:${codeqlHome}/codeql:${env.PATH}"]) {
                            checks.run('CodeQL Report') { logFile ->
                                execution.loggedShell("""
                                    mkdir -p ${env.SB_NAME}/codeql ${env.SB_NAME}/sonar/codeql
                                    CODEQL_BIN="\$(command -v codeql || true)"
                                    if [ -z "\$CODEQL_BIN" ]; then
                                        CODEQL_BIN="\$(find "\$CODEQL_HOME" -type f -name codeql | head -1)"
                                    fi
                                    "\$CODEQL_BIN" version
                                    "\$CODEQL_BIN" database create ${env.SB_NAME}/codeql/db-python \
                                      --language=python --source-root=. --overwrite
                                    "\$CODEQL_BIN" database analyze ${env.SB_NAME}/codeql/db-python \
                                      codeql/python-queries:codeql-suites/python-security-and-quality.qls \
                                      --format=sarif-latest --sarif-category=python \
                                      --output=${env.SB_NAME}/sonar/codeql/codeql-python.sarif
                                    "\$CODEQL_BIN" database create ${env.SB_NAME}/codeql/db-actions \
                                      --language=actions --source-root=. --overwrite
                                    "\$CODEQL_BIN" database analyze ${env.SB_NAME}/codeql/db-actions \
                                      codeql/actions-queries:codeql-suites/actions-security-and-quality.qls \
                                      --format=sarif-latest --sarif-category=actions \
                                      --output=${env.SB_NAME}/sonar/codeql/codeql-actions.sarif
                                """, logFile)
                                external.publishSarif("${env.SB_NAME}/sonar/codeql/codeql-python.sarif")
                                external.publishSarif("${env.SB_NAME}/sonar/codeql/codeql-actions.sarif")
                            }
                        }
                    }
                } finally {
                    stash name: 'report-codeql', includes: "${env.SB_NAME}/sonar/codeql/**", allowEmpty: true
                    stash name: 'qa-failure-marker-codeql', includes: '.ci-failures/codeql.failed', allowEmpty: true
                    archiveArtifacts artifacts: "${env.SB_NAME}/sonar/codeql/**", allowEmptyArchive: true
                }
            }
        }
    }
}

def osvGate(def scmConfig) {
    return {
        stage('OSV Scanner') {
            node('klymene') {
                try {
                    deleteDir()
                    checkout scmConfig
                    def checks = load 'jenkins/checks.groovy'
                    def execution = load 'jenkins/execution.groovy'
                    def external = load 'jenkins/external_results.groovy'
                    checks.run('OSV Scanner') { logFile ->
                        execution.loggedShell("""
                            mkdir -p ${env.SB_NAME}/sonar/osv
                            podman run --rm -v "\$PWD:/src:z" \
                              ghcr.io/google/osv-scanner:latest scan source \
                              -r --no-resolve --format sarif /src \
                              > ${env.SB_NAME}/sonar/osv/osv-scanner.sarif
                            test -s ${env.SB_NAME}/sonar/osv/osv-scanner.sarif
                        """, logFile)
                        external.publishSarif(
                            "${env.SB_NAME}/sonar/osv/osv-scanner.sarif",
                            'OSV-Scanner'
                        )
                        execution.loggedShell(
                            'podman run --rm -v "$PWD:/src:z" ghcr.io/google/osv-scanner:latest scan source -r --no-resolve /src',
                            logFile
                        )
                    }
                } finally {
                    archiveArtifacts artifacts: "${env.SB_NAME}/sonar/osv/**", allowEmptyArchive: true
                }
            }
        }
    }
}

def branches(def scmConfig) {
    return [
        gitleaks: gitleaksBranch(scmConfig),
        trivy: trivyBranch(),
        codeql: codeqlBranch(scmConfig)
    ]
}

return this
