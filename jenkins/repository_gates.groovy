def repositoryRulesBranch(def scmConfig) {
    return {
        stage('Repository Rules') {
            node('klymene') {
                deleteDir()
                checkout scmConfig
                def checks = load 'jenkins/checks.groovy'
                def execution = load 'jenkins/execution.groovy'
                checks.run('Repository Rules') { logFile ->
                    execution.inCi('''
                        if [ -n "${CHANGE_TARGET:-}" ]; then
                            git fetch origin "${CHANGE_TARGET}:refs/remotes/origin/${CHANGE_TARGET}" || true
                            RANGE="$(git merge-base HEAD "origin/${CHANGE_TARGET}" || git rev-parse HEAD^)..HEAD"
                        elif [ -n "${GIT_PREVIOUS_SUCCESSFUL_COMMIT:-}" ] && git rev-parse --verify "${GIT_PREVIOUS_SUCCESSFUL_COMMIT}^{commit}" >/dev/null 2>&1; then
                            RANGE="${GIT_PREVIOUS_SUCCESSFUL_COMMIT}..HEAD"
                        else
                            RANGE="HEAD^..HEAD"
                        fi
                        echo "Commit range: ${RANGE}"
                        python3 tools/check_commit_messages.py "${RANGE}"
                        python3 tools/check_release_notes.py custom_components/teltonika_rms/manifest.json CHANGELOG.md
                    ''', '--env CHANGE_TARGET --env GIT_PREVIOUS_SUCCESSFUL_COMMIT', logFile)
                }
            }
        }
    }
}

def hassfestBranch() {
    return {
        stage('Hassfest') {
            node('klymene') {
                deleteDir()
                unstash 'source'
                def checks = load 'jenkins/checks.groovy'
                def execution = load 'jenkins/execution.groovy'
                checks.run('Hassfest') { logFile ->
                    execution.loggedShell(
                        'podman run --rm -v "$PWD:/github/workspace:z" ghcr.io/home-assistant/hassfest:latest',
                        logFile
                    )
                }
            }
        }
    }
}

def actionlintBranch(def scmConfig) {
    return {
        stage('Actionlint') {
            node('klymene') {
                deleteDir()
                checkout scmConfig
                def checks = load 'jenkins/checks.groovy'
                def execution = load 'jenkins/execution.groovy'
                checks.run('Actionlint') { logFile ->
                    execution.loggedShell(
                        'podman run --rm -v "$PWD:/repo:z" -w /repo docker.io/rhysd/actionlint:latest',
                        logFile
                    )
                }
            }
        }
    }
}


def lockfileBranch() {
    return {
        stage('Lockfile Consistency') {
            node('klymene') {
                deleteDir()
                unstash 'source'
                def checks = load 'jenkins/checks.groovy'
                def execution = load 'jenkins/execution.groovy'
                checks.run('Lockfile Consistency') { logFile ->
                    execution.inCi(
                        'tools/compile_lockfile.sh --check',
                        '',
                        logFile
                    )
                }
            }
        }
    }
}

def branches(def scmConfig) {
    return [
        repositoryRules: repositoryRulesBranch(scmConfig),
        hassfest: hassfestBranch(),
        actionlint: actionlintBranch(scmConfig),
        lockfile: lockfileBranch()
    ]
}

return this
