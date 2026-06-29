void loggedShell(String command, String logFile) {
    writeFile(
        file: '.ci-host-command.sh',
        text: "#!/usr/bin/env bash\nset -euo pipefail\n${command}\n"
    )
    sh """
        chmod 700 .ci-host-command.sh
        bash -o pipefail -c './.ci-host-command.sh 2>&1 | tee -a "${logFile}"'
    """
}

void normalizeWorkspace(String logFile = '') {
    def command = '''
        set +e
        PARENT_DIR="$(dirname "$WORKSPACE")"
        WORKSPACE_NAME="$(basename "$WORKSPACE")"
        WORKSPACE_BASE="${WORKSPACE_NAME%%@*}"
        USER_ID="$(id -u)"
        GROUP_ID="$(id -g)"
        for path in "$PARENT_DIR/$WORKSPACE_BASE" "$PARENT_DIR/$WORKSPACE_BASE"@*; do
            [ -e "$path" ] || continue
            echo "Normalizing workspace permissions: $path"
            sudo chown -R "$USER_ID:$GROUP_ID" "$path" || true
            sudo chmod -R u+rwX "$path" || true
        done
    '''
    if (logFile) {
        loggedShell(command, logFile)
    } else {
        sh command
    }
}

void inCi(String command, String environmentOptions = '', String logFile = '') {
    writeFile(
        file: '.ci-command.sh',
        text: "#!/bin/sh\nset -eu\n${command}\n"
    )
    def hostCommand = """
        chmod 700 .ci-command.sh
        podman run --rm --pull=never ${environmentOptions} \\
          -v "\$PWD:/build:z" \\
          -w /build ${env.CI_IMAGE} \\
          /bin/sh /build/.ci-command.sh
    """
    if (logFile) {
        loggedShell(hostCommand, logFile)
    } else {
        sh hostCommand
    }
}

void reportStage(String markerName, Closure body) {
    catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
        try {
            body()
        } catch (err) {
            sh "mkdir -p .ci-failures && touch .ci-failures/${markerName}.failed"
            throw err
        }
    }
}

void unstashOptional(String stashName) {
    catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
        unstash stashName
    }
}

return this
