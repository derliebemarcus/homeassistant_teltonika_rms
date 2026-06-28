void checkoutRepo() {
    checkout scmGit(
        branches: [[name: env.BRANCH_NAME ? "*/${env.BRANCH_NAME}" : '*/main']],
        extensions: [cloneOption(noTags: false, shallow: false, depth: 0)],
        userRemoteConfigs: [[
            url: 'https://github.com/derliebemarcus/homeassistant_teltonika_rms.git',
            credentialsId: 'github token'
        ]]
    )
}

String sourceIncludes() {
    return 'CHANGELOG.md,CONTRIBUTING.md,custom_components/**,hacs.json,Jenkinsfile,LICENSE,Makefile,osv-scanner.toml,pyproject.toml,pytest.ini,README.md,requirements-dev.in,requirements.txt,ROADMAP.md,tests/**,tools/**,.coveragerc,.flake8,.githooks/**,.github/**,.gitignore,.gitleaksignore,.trivyignore'
}

String stageCheckName(String stageName) {
    return "Jenkins / ${stageName}"
}

String stageLogFile(String stageName) {
    def slug = stageName.toLowerCase().replaceAll('[^a-z0-9]+', '-').replaceAll('^-|-$', '')
    return ".ci-stage-logs/${slug}.log"
}

String stageLogExcerpt(String logFile) {
    if (!fileExists(logFile)) {
        return 'No command output was captured. Open the Jenkins console for the complete stage log.'
    }

    def output = readFile(file: logFile).trim()
    if (!output) {
        return 'The command completed without producing output. Open the Jenkins console for the complete stage log.'
    }

    final int maximumLength = 12000
    if (output.length() > maximumLength) {
        output = "... output truncated; showing the last ${maximumLength} characters ...\n" +
            output.substring(output.length() - maximumLength)
    }

    output = output.replace('```', '` ` `')
    return "### Stage log excerpt\n\n```text\n${output}\n```"
}

void publishStageCheck(String stageName, String status, String conclusion = '', String logFile = '', String errorMessage = '') {
    def checkName = stageCheckName(stageName)
    def detailsUrl = "${env.BUILD_URL}console"

    if (status == 'IN_PROGRESS') {
        publishChecks(
            name: checkName,
            title: "${stageName} is running",
            summary: "Jenkins build [#${env.BUILD_NUMBER}](${env.BUILD_URL}) is executing this stage.",
            detailsURL: detailsUrl,
            status: 'IN_PROGRESS'
        )
        return
    }

    def title = conclusion == 'SUCCESS' ? "${stageName} passed" :
        (conclusion == 'CANCELED' ? "${stageName} was cancelled" : "${stageName} failed")
    def summary = "Result: **${conclusion}**\n\nJenkins build: [#${env.BUILD_NUMBER}](${env.BUILD_URL})"
    if (errorMessage) {
        def safeErrorMessage = errorMessage.take(500).replace('`', ' ')
        summary += "\n\nFailure: ${safeErrorMessage}"
    }

    publishChecks(
        name: checkName,
        title: title,
        summary: summary,
        text: stageLogExcerpt(logFile),
        detailsURL: detailsUrl,
        conclusion: conclusion,
        status: 'COMPLETED'
    )
}

void withStageCheck(String stageName, Closure body) {
    def logFile = stageLogFile(stageName)
    sh "mkdir -p .ci-stage-logs && : > '${logFile}'"
    publishStageCheck(stageName, 'IN_PROGRESS')

    try {
        body(logFile)
        publishStageCheck(stageName, 'COMPLETED', 'SUCCESS', logFile)
    } catch (err) {
        def conclusion = currentBuild.currentResult == 'ABORTED' ? 'CANCELED' : 'FAILURE'
        writeFile(file: '.ci-stage-error.txt', text: "Pipeline exception: ${err}\n")
        sh "cat .ci-stage-error.txt >> '${logFile}'"
        publishStageCheck(stageName, 'COMPLETED', conclusion, logFile, err.toString())
        throw err
    }
}

void runLoggedShell(String command, String logFile) {
    writeFile(
        file: '.ci-host-command.sh',
        text: "#!/usr/bin/env bash\nset -euo pipefail\n${command}\n"
    )
    sh """
        chmod 700 .ci-host-command.sh
        bash -o pipefail -c './.ci-host-command.sh 2>&1 | tee -a "${logFile}"'
    """
}

void normalizeWorkspacePermissions(String logFile = '') {
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
        runLoggedShell(command, logFile)
    } else {
        sh command
    }
}

void runInCi(String command, String environmentOptions = '', String logFile = '') {
    writeFile(
        file: '.ci-command.sh',
        text: "#!/bin/sh\nset -eu\n${command}\n"
    )

    def hostCommand = """
        chmod 700 .ci-command.sh
        podman run --rm --pull=never \\
          ${environmentOptions} \\
          -v "\$PWD:/build:z" \\
          -w /build \\
          ${env.CI_IMAGE} \\
          /bin/sh /build/.ci-command.sh
    """

    if (logFile) {
        runLoggedShell(hostCommand, logFile)
    } else {
        sh hostCommand
    }
}

void markReportFailure(String markerName, Closure body) {
    try {
        body()
    } catch (err) {
        sh "mkdir -p .ci-failures && touch .ci-failures/${markerName}.failed"
        throw err
    }
}

void runReportStage(String markerName, Closure body) {
    catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
        markReportFailure(markerName) {
            body()
        }
    }
}

void unstashIfAvailable(String stashName) {
    catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
        unstash stashName
    }
}

pipeline {
    agent none

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout()
    }

    environment {
        CI_BASE_IMAGE = 'registry.home.siczb.de/siczb/python-ci:latest'
        CI_IMAGE = "registry.home.siczb.de/siczb/teltonika-rms-ci:${env.BUILD_NUMBER}"
        CI_REGISTRY = 'https://registry.home.siczb.de'
        PYPI_URL = 'https://artifacts.home.siczb.de/repository/pypi-proxy/simple/'
        GITHUB_OWNER = 'derliebemarcus'
        GITHUB_REPO = 'homeassistant_teltonika_rms'
        SB_NAME = "build_sb_${env.BUILD_NUMBER}"
        CAPTURED_SHA = ''
        COMMIT_HASH = ''
        VERSION = ''
    }

    stages {
        stage('Initialize & Stash') {
            agent { label 'klymene' }
            steps {
                script {
                    normalizeWorkspacePermissions()
                    deleteDir()
                    checkoutRepo()
                    withStageCheck('Initialize & Stash') { logFile ->
                        env.CAPTURED_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                        env.COMMIT_HASH = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                        env.VERSION = sh(
                            script: '''
                                python3 - <<'PY'
import json
from pathlib import Path
print(json.loads(Path("custom_components/teltonika_rms/manifest.json").read_text(encoding="utf-8"))["version"])
PY
                            ''',
                            returnStdout: true
                        ).trim()
                        runLoggedShell('''
                            if grep -R "<<<<<<<\\|=======\\|>>>>>>>" requirements*.txt requirements*.in pyproject.toml custom_components tests tools 2>/dev/null; then
                                echo "Merge conflict markers detected."
                                exit 1
                            fi
                            echo "Commit: ${CAPTURED_SHA}"
                            echo "Version: ${VERSION}"
                        ''', logFile)
                        stash name: 'source', includes: sourceIncludes(), useDefaultExcludes: false
                    }
                }
            }
        }

        stage('Build CI Environment') {
            agent { label 'klymene' }
            steps {
                script {
                    normalizeWorkspacePermissions()
                    deleteDir()
                    unstash 'source'
                    withStageCheck('Build CI Environment') { logFile ->
                        runLoggedShell("""cat <<'DOCKERFILE' > Dockerfile.ci
FROM ${env.CI_BASE_IMAGE}
WORKDIR /build
USER root
RUN (apt-get update && apt-get install -y git curl ca-certificates) || (apk add --no-cache git curl ca-certificates) || true
COPY requirements.txt ./
RUN python3 -m pip install --upgrade pip --index-url ${env.PYPI_URL}
RUN python3 -m pip install --index-url ${env.PYPI_URL} -r requirements.txt
COPY pyproject.toml pytest.ini .coveragerc ./
COPY custom_components ./custom_components
COPY tests ./tests
COPY tools ./tools
DOCKERFILE
podman build --pull=never -t ${env.CI_IMAGE} -f Dockerfile.ci .
""", logFile)
                        withCredentials([usernamePassword(credentialsId: 'harbor-jenkins-user', usernameVariable: 'U', passwordVariable: 'P')]) {
                            runLoggedShell("""
                                podman login -u "\$U" -p "\$P" registry.home.siczb.de
                                podman push ${env.CI_IMAGE}
                            """, logFile)
                        }
                    }
                }
            }
        }

        stage('Normalize Jenkins Workspaces') {
            agent { label 'klymene' }
            steps {
                script {
                    withStageCheck('Normalize Jenkins Workspaces') { logFile ->
                        normalizeWorkspacePermissions(logFile)
                    }
                }
            }
        }

        stage('Parallel: Report-Producing QA') {
            failFast false
            parallel {
                stage('Pytest Coverage Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('pytest-coverage') {
                                deleteDir()
                                unstash 'source'
                                withStageCheck('Pytest Coverage Report') { logFile ->
                                    runInCi("""
                                        mkdir -p ${env.SB_NAME}/sonar/tests
                                        python3 -m pytest tests/unit tests/ha \\
                                          --junitxml=${env.SB_NAME}/sonar/tests/pytest.xml \\
                                          --cov=. --cov-config=.coveragerc \\
                                          --cov-report=xml:${env.SB_NAME}/sonar/tests/coverage.xml \\
                                          --cov-report=term-missing
                                        python3 tools/check_coverage_threshold.py ${env.SB_NAME}/sonar/tests/coverage.xml 97.1
                                    """, '', logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-pytest-coverage', includes: "${env.SB_NAME}/sonar/tests/**", allowEmpty: true
                            stash name: 'qa-failure-marker-pytest-coverage', includes: '.ci-failures/pytest-coverage.failed', allowEmpty: true
                            junit allowEmptyResults: true, testResults: "${env.SB_NAME}/sonar/tests/pytest.xml"
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/tests/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Ruff Lint Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('ruff-lint') {
                                deleteDir()
                                unstash 'source'
                                withStageCheck('Ruff Lint Report') { logFile ->
                                    runInCi("mkdir -p ${env.SB_NAME}/sonar/ruff && python3 -m ruff check . --output-format=json --output-file=${env.SB_NAME}/sonar/ruff/ruff-report.json", '', logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-ruff-lint', includes: "${env.SB_NAME}/sonar/ruff/**", allowEmpty: true
                            stash name: 'qa-failure-marker-ruff-lint', includes: '.ci-failures/ruff-lint.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/ruff/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Ruff Format Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('ruff-format') {
                                deleteDir()
                                unstash 'source'
                                withStageCheck('Ruff Format Report') { logFile ->
                                    runInCi("""
                                        mkdir -p ${env.SB_NAME}/sonar/ruff-format
                                        status=0
                                        python3 -m ruff format --check . > ${env.SB_NAME}/sonar/ruff-format/ruff-format.txt 2>&1 || status=\$?
                                        cat ${env.SB_NAME}/sonar/ruff-format/ruff-format.txt
                                        exit \$status
                                    """, '', logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-ruff-format', includes: "${env.SB_NAME}/sonar/ruff-format/**", allowEmpty: true
                            stash name: 'qa-failure-marker-ruff-format', includes: '.ci-failures/ruff-format.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/ruff-format/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Mypy Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('mypy') {
                                deleteDir()
                                unstash 'source'
                                withStageCheck('Mypy Report') { logFile ->
                                    runInCi("""
                                        mkdir -p ${env.SB_NAME}/sonar/mypy
                                        status=0
                                        python3 -m mypy . --show-column-numbers > ${env.SB_NAME}/sonar/mypy/mypy-report.txt 2>&1 || status=\$?
                                        cat ${env.SB_NAME}/sonar/mypy/mypy-report.txt
                                        exit \$status
                                    """, '', logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-mypy', includes: "${env.SB_NAME}/sonar/mypy/**", allowEmpty: true
                            stash name: 'qa-failure-marker-mypy', includes: '.ci-failures/mypy.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/mypy/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Translation Validation Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('translations') {
                                deleteDir()
                                unstash 'source'
                                withStageCheck('Translation Validation Report') { logFile ->
                                    runInCi("""
                                        mkdir -p ${env.SB_NAME}/sonar/translations
                                        status=0
                                        python3 tools/check_translations.py > ${env.SB_NAME}/sonar/translations/translations.txt 2>&1 || status=\$?
                                        cat ${env.SB_NAME}/sonar/translations/translations.txt
                                        exit \$status
                                    """, '', logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-translations', includes: "${env.SB_NAME}/sonar/translations/**", allowEmpty: true
                            stash name: 'qa-failure-marker-translations', includes: '.ci-failures/translations.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/translations/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Pip Audit Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('pip-audit') {
                                deleteDir()
                                unstash 'source'
                                withStageCheck('Pip Audit Report') { logFile ->
                                    runInCi("""
                                        mkdir -p ${env.SB_NAME}/sonar/pip-audit
                                        python3 tools/run_pip_audit.py -r requirements.txt --format json --output ${env.SB_NAME}/sonar/pip-audit/pip-audit-report.json
                                    """, '', logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-pip-audit', includes: "${env.SB_NAME}/sonar/pip-audit/**", allowEmpty: true
                            stash name: 'qa-failure-marker-pip-audit', includes: '.ci-failures/pip-audit.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/pip-audit/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Gitleaks Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('gitleaks') {
                                deleteDir()
                                checkoutRepo()
                                withStageCheck('Gitleaks Report') { logFile ->
                                    runLoggedShell("""
                                        mkdir -p ${env.SB_NAME}/sonar/gitleaks
                                        podman run --rm -v "\$PWD:/repo:z" -w /repo docker.io/zricethezav/gitleaks:latest detect --source=/repo --redact --verbose --report-format=json --report-path=${env.SB_NAME}/sonar/gitleaks/gitleaks-report.json
                                    """, logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-gitleaks', includes: "${env.SB_NAME}/sonar/gitleaks/**", allowEmpty: true
                            stash name: 'qa-failure-marker-gitleaks', includes: '.ci-failures/gitleaks.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/gitleaks/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Trivy FS Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('trivy') {
                                deleteDir()
                                unstash 'source'
                                withStageCheck('Trivy FS Report') { logFile ->
                                    runLoggedShell("""
                                        mkdir -p ${env.SB_NAME}/sonar/trivy
                                        podman run --rm -v "\$PWD:/app:z" -w /app docker.io/aquasec/trivy:latest fs . --severity HIGH,CRITICAL --format json --output ${env.SB_NAME}/sonar/trivy/trivy-report.json --no-progress
                                    """, logFile)
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-trivy', includes: "${env.SB_NAME}/sonar/trivy/**", allowEmpty: true
                            stash name: 'qa-failure-marker-trivy', includes: '.ci-failures/trivy.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/trivy/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('CodeQL Report') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            runReportStage('codeql') {
                                deleteDir()
                                unstash 'source'
                                def codeqlHome = tool name: 'codeql'
                                withEnv(["CODEQL_HOME=${codeqlHome}", "PATH=${codeqlHome}:${codeqlHome}/codeql:${env.PATH}"]) {
                                    withStageCheck('CodeQL Report') { logFile ->
                                        runLoggedShell("""
                                            set -eu
                                            mkdir -p ${env.SB_NAME}/codeql ${env.SB_NAME}/sonar/codeql
                                            CODEQL_BIN="\$(command -v codeql || true)"
                                            if [ -z "\$CODEQL_BIN" ]; then CODEQL_BIN="\$(find "\$CODEQL_HOME" -type f -name codeql | head -1)"; fi
                                            "\$CODEQL_BIN" version
                                            "\$CODEQL_BIN" database create ${env.SB_NAME}/codeql/db-python --language=python --source-root=. --overwrite
                                            "\$CODEQL_BIN" database analyze ${env.SB_NAME}/codeql/db-python codeql/python-queries:codeql-suites/python-security-and-quality.qls --format=sarif-latest --sarif-category=python --output=${env.SB_NAME}/sonar/codeql/codeql-python.sarif
                                        """, logFile)
                                    }
                                }
                            }
                        }
                    }
                    post {
                        always {
                            stash name: 'report-codeql', includes: "${env.SB_NAME}/sonar/codeql/**", allowEmpty: true
                            stash name: 'qa-failure-marker-codeql', includes: '.ci-failures/codeql.failed', allowEmpty: true
                            archiveArtifacts artifacts: "${env.SB_NAME}/sonar/codeql/**", allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Parallel: Blocking Gates') {
            failFast false
            parallel {
                stage('SonarQube Scan') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            deleteDir()
                            unstash 'source'
                            ['report-pytest-coverage', 'report-ruff-lint', 'report-ruff-format', 'report-mypy', 'report-translations', 'report-pip-audit', 'report-gitleaks', 'report-trivy', 'report-codeql'].each { unstashIfAvailable(it) }
                            withStageCheck('SonarQube Scan') { logFile ->
                                runLoggedShell("mkdir -p ${env.SB_NAME}/sonar && find ${env.SB_NAME}/sonar -type f | sort || true", logFile)
                                withSonarQubeEnv('SonarQube') {
                                    withCredentials([string(credentialsId: 'Sonarqube', variable: 'SONAR_TOKEN')]) {
                                        runInCi("""
                                            SONAR_BIN="\$(command -v sonar-scanner || true)"
                                            if [ -z "\$SONAR_BIN" ] && command -v pysonar >/dev/null 2>&1; then SONAR_BIN="\$(command -v pysonar)"; fi
                                            if [ -z "\$SONAR_BIN" ]; then echo "Neither sonar-scanner nor pysonar is available in the CI image."; exit 1; fi
                                            SONAR_ARGS="-Dsonar.host.url=https://sonarqube.home.siczb.de -Dsonar.token=\${SONAR_TOKEN} -Dsonar.projectKey=teltonika_rms -Dsonar.projectName=teltonika_rms -Dsonar.projectVersion=${env.VERSION}-${env.COMMIT_HASH} -Dsonar.python.version=3.14 -Dsonar.sources=custom_components/teltonika_rms -Dsonar.tests=tests"
                                            if [ -f "${env.SB_NAME}/sonar/tests/coverage.xml" ]; then SONAR_ARGS="\$SONAR_ARGS -Dsonar.python.coverage.reportPaths=${env.SB_NAME}/sonar/tests/coverage.xml"; fi
                                            if [ -f "${env.SB_NAME}/sonar/tests/pytest.xml" ]; then SONAR_ARGS="\$SONAR_ARGS -Dsonar.python.xunit.reportPath=${env.SB_NAME}/sonar/tests/pytest.xml"; fi
                                            "\$SONAR_BIN" \$SONAR_ARGS
                                        """, '--env SONAR_TOKEN', logFile)
                                    }
                                }
                            }
                        }
                    }
                }

                stage('Mutation Testing') {
                    agent { label 'klymene' }
                    options { timeout(time: 45, unit: 'MINUTES') }
                    steps {
                        script {
                            deleteDir()
                            unstash 'source'
                            withStageCheck('Mutation Testing') { logFile ->
                                runInCi("""
                                    mkdir -p ${env.SB_NAME}/mutation
                                    python3 -m pytest --cov=custom_components/teltonika_rms --cov-context=test --cov-config=.coveragerc tests/
                                    python3 -m mutmut run
                                    python3 -m mutmut results > ${env.SB_NAME}/mutation/mutation-results.txt || true
                                """, '', logFile)
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: "${env.SB_NAME}/mutation/**,mutants/.mutmut-cache/**", allowEmptyArchive: true
                        }
                    }
                }

                stage('Repository Rules') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            deleteDir()
                            checkoutRepo()
                            withStageCheck('Repository Rules') { logFile ->
                                runInCi('''
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

                stage('Hassfest') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            deleteDir()
                            unstash 'source'
                            withStageCheck('Hassfest') { logFile ->
                                runLoggedShell('podman run --rm -v "$PWD:/github/workspace:z" ghcr.io/home-assistant/hassfest:latest', logFile)
                            }
                        }
                    }
                }

                stage('OSV Scanner') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            deleteDir()
                            unstash 'source'
                            withStageCheck('OSV Scanner') { logFile ->
                                runLoggedShell('podman run --rm -v "$PWD:/src:z" ghcr.io/google/osv-scanner:latest scan source -r --no-resolve /src', logFile)
                            }
                        }
                    }
                }

                stage('Actionlint') {
                    agent { label 'klymene' }
                    steps {
                        script {
                            deleteDir()
                            checkoutRepo()
                            withStageCheck('Actionlint') { logFile ->
                                runLoggedShell('podman run --rm -v "$PWD:/repo:z" -w /repo docker.io/rhysd/actionlint:latest', logFile)
                            }
                        }
                    }
                }
            }
        }

        stage('Finalize Quality Gate Result') {
            agent { label 'klymene' }
            steps {
                script {
                    normalizeWorkspacePermissions()
                    deleteDir()
                    ['qa-failure-marker-pytest-coverage', 'qa-failure-marker-ruff-lint', 'qa-failure-marker-ruff-format', 'qa-failure-marker-mypy', 'qa-failure-marker-translations', 'qa-failure-marker-pip-audit', 'qa-failure-marker-gitleaks', 'qa-failure-marker-trivy', 'qa-failure-marker-codeql'].each { unstashIfAvailable(it) }
                    withStageCheck('Finalize Quality Gate Result') { logFile ->
                        runLoggedShell('find .ci-failures -type f -print 2>/dev/null || true', logFile)
                        def failedReports = sh(script: 'test -d .ci-failures && find .ci-failures -type f | wc -l || echo 0', returnStdout: true).trim()
                        if (failedReports != '0') {
                            error('One or more report-producing QA stages failed. See .ci-failures markers and archived reports.')
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                def buildResult = currentBuild.currentResult ?: 'SUCCESS'
                def githubStatus = buildResult == 'ABORTED' ? 'FAILURE' : buildResult
                def checksConclusion = buildResult == 'SUCCESS' ? 'SUCCESS' : (buildResult == 'UNSTABLE' ? 'NEUTRAL' : (buildResult == 'ABORTED' ? 'CANCELED' : 'FAILURE'))
                githubNotify(
                    credentialsId: 'github token',
                    status: githubStatus,
                    context: 'Continuous Integration / Jenkins',
                    description: "Build ${buildResult}",
                    account: env.GITHUB_OWNER,
                    repo: env.GITHUB_REPO,
                    sha: env.CAPTURED_SHA ?: 'main'
                )
                publishChecks(
                    name: 'Jenkins Build',
                    title: 'Teltonika RMS Quality Gates',
                    summary: "Status: ${buildResult}\n\nIndividual Jenkins stages are published as separate checks.",
                    detailsURL: "${env.BUILD_URL}console",
                    conclusion: checksConclusion,
                    status: 'COMPLETED'
                )
                node('klymene') {
                    normalizeWorkspacePermissions()
                    sh "podman rmi ${env.CI_IMAGE} || true"
                }
            }
        }
    }
}
