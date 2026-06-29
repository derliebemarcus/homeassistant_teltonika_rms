void runGate() {
    stage('Finalize Quality Gate Result') {
        node('klymene') {
            def execution = load 'jenkins/execution.groovy'
            def checks = load 'jenkins/checks.groovy'
            execution.normalizeWorkspace()
            deleteDir()
            [
                'qa-failure-marker-pytest-coverage',
                'qa-failure-marker-ruff-lint',
                'qa-failure-marker-ruff-format',
                'qa-failure-marker-mypy',
                'qa-failure-marker-translations',
                'qa-failure-marker-pip-audit',
                'qa-failure-marker-gitleaks',
                'qa-failure-marker-trivy',
                'qa-failure-marker-codeql'
            ].each { execution.unstashOptional(it) }
            checks.run('Finalize Quality Gate Result') { logFile ->
                execution.loggedShell(
                    'find .ci-failures -type f -print 2>/dev/null || true',
                    logFile
                )
                def failedReports = sh(
                    script: 'test -d .ci-failures && find .ci-failures -type f | wc -l || echo 0',
                    returnStdout: true
                ).trim()
                if (failedReports != '0') {
                    error('One or more report-producing QA stages failed. See .ci-failures markers and archived reports.')
                }
            }
        }
    }
}

return this
