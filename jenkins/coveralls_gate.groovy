def branch() {
    return {
        stage('Coveralls Upload') {
            node('klymene') {
                deleteDir()
                unstash 'source'
                unstash 'report-pytest-coverage'
                def checks = load 'jenkins/checks.groovy'
                def execution = load 'jenkins/execution.groovy'
                def external = load 'jenkins/external_results.groovy'
                checks.run('Coveralls Upload') { logFile ->
                    execution.loggedShell(
                        "test -s ${env.SB_NAME}/sonar/tests/coverage.xml",
                        logFile
                    )
                    external.publishCoveralls("${env.SB_NAME}/sonar/tests/coverage.xml")
                }
            }
        }
    }
}

return this
