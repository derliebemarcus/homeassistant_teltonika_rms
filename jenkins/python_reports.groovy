def reportBranch(
    String stageName,
    String markerName,
    String taskName,
    String artifactPath,
    String failureMarker,
    String junitPath = ''
) {
    return {
        stage(stageName) {
            node('klymene') {
                try {
                    deleteDir()
                    unstash 'source'
                    def checks = load 'jenkins/checks.groovy'
                    def execution = load 'jenkins/execution.groovy'
                    execution.reportStage(markerName) {
                        checks.run(stageName) { logFile ->
                            execution.inCi(
                                "chmod 700 tools/jenkins_python_tasks.sh && tools/jenkins_python_tasks.sh ${taskName}",
                                '--env SB_NAME',
                                logFile
                            )
                        }
                    }
                } finally {
                    stash name: "report-${markerName}", includes: artifactPath, allowEmpty: true
                    stash name: "qa-failure-marker-${markerName}", includes: failureMarker, allowEmpty: true
                    if (junitPath) {
                        junit allowEmptyResults: true, testResults: junitPath
                    }
                    archiveArtifacts artifacts: artifactPath, allowEmptyArchive: true
                }
            }
        }
    }
}

def branches() {
    return [
        pytest: reportBranch(
            'Pytest Coverage Report',
            'pytest-coverage',
            'pytest',
            "${env.SB_NAME}/sonar/tests/**",
            '.ci-failures/pytest-coverage.failed',
            "${env.SB_NAME}/sonar/tests/pytest.xml"
        ),
        ruffLint: reportBranch(
            'Ruff Lint Report',
            'ruff-lint',
            'ruff-lint',
            "${env.SB_NAME}/sonar/ruff/**",
            '.ci-failures/ruff-lint.failed'
        ),
        ruffFormat: reportBranch(
            'Ruff Format Report',
            'ruff-format',
            'ruff-format',
            "${env.SB_NAME}/sonar/ruff-format/**",
            '.ci-failures/ruff-format.failed'
        ),
        mypy: reportBranch(
            'Mypy Report',
            'mypy',
            'mypy',
            "${env.SB_NAME}/sonar/mypy/**",
            '.ci-failures/mypy.failed'
        ),
        translations: reportBranch(
            'Translation Validation Report',
            'translations',
            'translations',
            "${env.SB_NAME}/sonar/translations/**",
            '.ci-failures/translations.failed'
        ),
        pipAudit: reportBranch(
            'Pip Audit Report',
            'pip-audit',
            'pip-audit',
            "${env.SB_NAME}/sonar/pip-audit/**",
            '.ci-failures/pip-audit.failed'
        )
    ]
}

return this
