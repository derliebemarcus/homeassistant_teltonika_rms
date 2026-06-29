def branch() {
    return {
        stage('Mutation Testing') {
            node('klymene') {
                try {
                    timeout(time: 45, unit: 'MINUTES') {
                        deleteDir()
                        unstash 'source'
                        def checks = load 'jenkins/checks.groovy'
                        def execution = load 'jenkins/execution.groovy'
                        checks.run('Mutation Testing') { logFile ->
                            execution.inCi("""
                                mkdir -p ${env.SB_NAME}/mutation
                                python3 -m pytest \
                                  --cov=custom_components/teltonika_rms \
                                  --cov-context=test \
                                  --cov-config=.coveragerc \
                                  tests/
                                python3 -m mutmut run
                                python3 -m mutmut results \
                                  > ${env.SB_NAME}/mutation/mutation-results.txt || true
                            """, '', logFile)
                        }
                    }
                } finally {
                    archiveArtifacts(
                        artifacts: "${env.SB_NAME}/mutation/**,mutants/.mutmut-cache/**",
                        allowEmptyArchive: true
                    )
                }
            }
        }
    }
}

return this
