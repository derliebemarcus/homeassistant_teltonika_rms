void checkoutRepo() {
    checkout scmGit(
        branches: [[name: env.BRANCH_NAME ? "*/${env.BRANCH_NAME}" : '*/main']],
        extensions: [cloneOption(noTags: false, shallow: false, depth: 0)],
        userRemoteConfigs: [[
            url: 'https://github.com/derliebemarcus/teltonika_rms.git',
            credentialsId: 'github token'
        ]]
    )
}

String sourceIncludes() {
    return 'CHANGELOG.md,CONTRIBUTING.md,custom_components/**,hacs.json,Jenkinsfile,LICENSE,Makefile,osv-scanner.toml,pyproject.toml,pytest.ini,README.md,requirements-dev.txt,requirements.txt,ROADMAP.md,tests/**,tools/**,.coveragerc,.flake8,.githooks/**,.github/**,.gitignore,.gitleaksignore,.trivyignore'
}

void normalizeWorkspacePermissions() {
    sh '''
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
        GITHUB_REPO = 'teltonika_rms'
        SB_NAME = "build_sb_${env.BUILD_NUMBER}"
        CURRENT_STAGE = 'Initialize'
        CAPTURED_SHA = ''
        COMMIT_HASH = ''
        VERSION = ''
    }

    stages {
        stage('Initialize & Stash') {
            agent { label 'klymene' }
            steps {
                script {
                    env.CURRENT_STAGE = 'Initialize & Stash'
                    normalizeWorkspacePermissions()
                    deleteDir()
                    checkoutRepo()
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
                    sh '''
                        if grep -R "<<<<<<<\\|=======\\|>>>>>>>" requirements*.txt pyproject.toml custom_components tests tools 2>/dev/null; then
                            echo "Merge conflict markers detected."
                            exit 1
                        fi
                    '''
                    stash name: 'source', includes: sourceIncludes(), useDefaultExcludes: false
                }
            }
        }

        stage('Build CI Environment') {
            agent { label 'klymene' }
            steps {
                script {
                    env.CURRENT_STAGE = 'Build CI Environment'
                    normalizeWorkspacePermissions()
                    deleteDir()
                    unstash 'source'
                    sh """
                        cat <<'EOF' > Dockerfile.ci
FROM ${env.CI_BASE_IMAGE}
WORKDIR /build
USER root
RUN (apt-get update && apt-get install -y git curl ca-certificates) || (apk add --no-cache git curl ca-certificates) || true
COPY requirements-dev.txt ./
RUN python3 -m pip install --upgrade pip --index-url ${env.PYPI_URL}
RUN python3 -m pip install --index-url ${env.PYPI_URL} -r requirements-dev.txt
COPY pyproject.toml pytest.ini .coveragerc ./
COPY custom_components ./custom_components
COPY tests ./tests
COPY tools ./tools
EOF
                        podman build --pull=never -t ${env.CI_IMAGE} -f Dockerfile.ci .
                    """
                    withCredentials([usernamePassword(credentialsId: 'harbor-jenkins-user', usernameVariable: 'U', passwordVariable: 'P')]) {
                        sh """
                            podman login -u "\$U" -p "\$P" registry.home.siczb.de
                            podman push ${env.CI_IMAGE}
                        """
                    }
                }
            }
        }

        stage('Normalize Jenkins Workspaces') {
            agent { label 'klymene' }
            steps {
                script {
                    env.CURRENT_STAGE = 'Normalize Jenkins Workspaces'
                    normalizeWorkspacePermissions()
                }
            }
        }

        stage('Parallel: Report-Producing QA') {
            failFast false
            parallel {
                stage('Pytest Coverage Report') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps {
                        script {
                            env.CURRENT_STAGE = 'Pytest Coverage Report'
                            runReportStage('pytest-coverage') {
                                deleteDir()
                                unstash 'source'
                                sh """
                                    mkdir -p ${env.SB_NAME}/sonar/tests
                                    python3 -m pytest tests/unit tests/ha \
                                      --junitxml=${env.SB_NAME}/sonar/tests/pytest.xml \
                                      --cov=. --cov-config=.coveragerc \
                                      --cov-report=xml:${env.SB_NAME}/sonar/tests/coverage.xml \
                                      --cov-report=term-missing
                                    python3 tools/check_coverage_threshold.py ${env.SB_NAME}/sonar/tests/coverage.xml 97.1
                                """
                            }
                        }
                    }
                    post { always { stash name: 'report-pytest-coverage', includes: "${env.SB_NAME}/sonar/tests/**", allowEmpty: true; stash name: 'qa-failure-marker-pytest-coverage', includes: '.ci-failures/pytest-coverage.failed', allowEmpty: true; junit allowEmptyResults: true, testResults: "${env.SB_NAME}/sonar/tests/pytest.xml"; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/tests/**", allowEmptyArchive: true } }
                }

                stage('Ruff Lint Report') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps { script { env.CURRENT_STAGE = 'Ruff Lint Report'; runReportStage('ruff-lint') { deleteDir(); unstash 'source'; sh "mkdir -p ${env.SB_NAME}/sonar/ruff && python3 -m ruff check . --output-format=json --output-file=${env.SB_NAME}/sonar/ruff/ruff-report.json" } } }
                    post { always { stash name: 'report-ruff-lint', includes: "${env.SB_NAME}/sonar/ruff/**", allowEmpty: true; stash name: 'qa-failure-marker-ruff-lint', includes: '.ci-failures/ruff-lint.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/ruff/**", allowEmptyArchive: true } }
                }

                stage('Ruff Format Report') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps { script { env.CURRENT_STAGE = 'Ruff Format Report'; runReportStage('ruff-format') { deleteDir(); unstash 'source'; sh """
                        mkdir -p ${env.SB_NAME}/sonar/ruff-format
                        python3 -m ruff format --check . > ${env.SB_NAME}/sonar/ruff-format/ruff-format.txt 2>&1
                        status=\$?
                        cat ${env.SB_NAME}/sonar/ruff-format/ruff-format.txt
                        exit \$status
                    """ } } }
                    post { always { stash name: 'report-ruff-format', includes: "${env.SB_NAME}/sonar/ruff-format/**", allowEmpty: true; stash name: 'qa-failure-marker-ruff-format', includes: '.ci-failures/ruff-format.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/ruff-format/**", allowEmptyArchive: true } }
                }

                stage('Mypy Report') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps { script { env.CURRENT_STAGE = 'Mypy Report'; runReportStage('mypy') { deleteDir(); unstash 'source'; sh """
                        mkdir -p ${env.SB_NAME}/sonar/mypy
                        python3 -m mypy . --show-column-numbers > ${env.SB_NAME}/sonar/mypy/mypy-report.txt 2>&1
                        status=\$?
                        cat ${env.SB_NAME}/sonar/mypy/mypy-report.txt
                        exit \$status
                    """ } } }
                    post { always { stash name: 'report-mypy', includes: "${env.SB_NAME}/sonar/mypy/**", allowEmpty: true; stash name: 'qa-failure-marker-mypy', includes: '.ci-failures/mypy.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/mypy/**", allowEmptyArchive: true } }
                }

                stage('Translation Validation Report') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps { script { env.CURRENT_STAGE = 'Translation Validation Report'; runReportStage('translations') { deleteDir(); unstash 'source'; sh """
                        mkdir -p ${env.SB_NAME}/sonar/translations
                        python3 tools/check_translations.py > ${env.SB_NAME}/sonar/translations/translations.txt 2>&1
                        status=\$?
                        cat ${env.SB_NAME}/sonar/translations/translations.txt
                        exit \$status
                    """ } } }
                    post { always { stash name: 'report-translations', includes: "${env.SB_NAME}/sonar/translations/**", allowEmpty: true; stash name: 'qa-failure-marker-translations', includes: '.ci-failures/translations.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/translations/**", allowEmptyArchive: true } }
                }

                stage('Pip Audit Report') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps { script { env.CURRENT_STAGE = 'Pip Audit Report'; runReportStage('pip-audit') { deleteDir(); unstash 'source'; sh """
                        mkdir -p ${env.SB_NAME}/sonar/pip-audit
                        python3 -m pip_audit -r requirements-dev.txt --format json --output ${env.SB_NAME}/sonar/pip-audit/pip-audit-report.json \
                          --ignore-vuln CVE-2025-67221 --ignore-vuln CVE-2026-32597 --ignore-vuln CVE-2026-27448 --ignore-vuln CVE-2026-27459 \
                          --ignore-vuln CVE-2026-4539 --ignore-vuln CVE-2026-25645 --ignore-vuln CVE-2026-34073 --ignore-vuln CVE-2026-39892 \
                          --ignore-vuln GHSA-pjjw-68hj-v9mw --ignore-vuln CVE-2026-34513 --ignore-vuln CVE-2026-34525 --ignore-vuln CVE-2026-34519 \
                          --ignore-vuln CVE-2026-34520 --ignore-vuln CVE-2026-34517
                    """ } } }
                    post { always { stash name: 'report-pip-audit', includes: "${env.SB_NAME}/sonar/pip-audit/**", allowEmpty: true; stash name: 'qa-failure-marker-pip-audit', includes: '.ci-failures/pip-audit.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/pip-audit/**", allowEmptyArchive: true } }
                }

                stage('Gitleaks Report') {
                    agent { label 'klymene' }
                    steps { script { env.CURRENT_STAGE = 'Gitleaks Report'; runReportStage('gitleaks') { deleteDir(); checkoutRepo(); sh """
                        mkdir -p ${env.SB_NAME}/sonar/gitleaks
                        podman run --rm -v "\$PWD:/repo:z" -w /repo docker.io/zricethezav/gitleaks:latest detect --source=/repo --redact --verbose --report-format=json --report-path=${env.SB_NAME}/sonar/gitleaks/gitleaks-report.json
                    """ } } }
                    post { always { stash name: 'report-gitleaks', includes: "${env.SB_NAME}/sonar/gitleaks/**", allowEmpty: true; stash name: 'qa-failure-marker-gitleaks', includes: '.ci-failures/gitleaks.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/gitleaks/**", allowEmptyArchive: true } }
                }

                stage('Trivy FS Report') {
                    agent { label 'klymene' }
                    steps { script { env.CURRENT_STAGE = 'Trivy FS Report'; runReportStage('trivy') { deleteDir(); unstash 'source'; sh """
                        mkdir -p ${env.SB_NAME}/sonar/trivy
                        podman run --rm -v "\$PWD:/app:z" -w /app docker.io/aquasec/trivy:latest fs . --severity HIGH,CRITICAL --format json --output ${env.SB_NAME}/sonar/trivy/trivy-report.json --no-progress
                    """ } } }
                    post { always { stash name: 'report-trivy', includes: "${env.SB_NAME}/sonar/trivy/**", allowEmpty: true; stash name: 'qa-failure-marker-trivy', includes: '.ci-failures/trivy.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/trivy/**", allowEmptyArchive: true } }
                }

                stage('CodeQL Report') {
                    agent { label 'klymene' }
                    steps { script { env.CURRENT_STAGE = 'CodeQL Report'; runReportStage('codeql') { deleteDir(); unstash 'source'; def codeqlHome = tool name: 'codeql'; withEnv(["CODEQL_HOME=${codeqlHome}", "PATH=${codeqlHome}:${codeqlHome}/codeql:${env.PATH}"]) { sh """
                        set -eu
                        mkdir -p ${env.SB_NAME}/codeql ${env.SB_NAME}/sonar/codeql
                        CODEQL_BIN="\$(command -v codeql || true)"
                        if [ -z "\$CODEQL_BIN" ]; then CODEQL_BIN="\$(find "\$CODEQL_HOME" -type f -name codeql | head -1)"; fi
                        "\$CODEQL_BIN" version
                        "\$CODEQL_BIN" database create ${env.SB_NAME}/codeql/db-python --language=python --source-root=. --overwrite
                        "\$CODEQL_BIN" database analyze ${env.SB_NAME}/codeql/db-python codeql/python-queries:codeql-suites/python-security-and-quality.qls --format=sarif-latest --sarif-category=python --output=${env.SB_NAME}/sonar/codeql/codeql-python.sarif
                    """ } } } }
                    post { always { stash name: 'report-codeql', includes: "${env.SB_NAME}/sonar/codeql/**", allowEmpty: true; stash name: 'qa-failure-marker-codeql', includes: '.ci-failures/codeql.failed', allowEmpty: true; archiveArtifacts artifacts: "${env.SB_NAME}/sonar/codeql/**", allowEmptyArchive: true } }
                }
            }
        }

        stage('Parallel: Blocking Gates') {
            failFast false
            parallel {
                stage('SonarQube Scan') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps { script {
                        env.CURRENT_STAGE = 'SonarQube Scan'
                        deleteDir()
                        unstash 'source'
                        ['report-pytest-coverage','report-ruff-lint','report-ruff-format','report-mypy','report-translations','report-pip-audit','report-gitleaks','report-trivy','report-codeql'].each { unstashIfAvailable(it) }
                        sh "mkdir -p ${env.SB_NAME}/sonar && find ${env.SB_NAME}/sonar -type f | sort || true"
                        withSonarQubeEnv('SonarQube') {
                            withCredentials([string(credentialsId: 'Sonarqube', variable: 'SONAR_TOKEN')]) {
                                sh """
                                    set -eu
                                    SONAR_BIN="\$(command -v sonar-scanner || true)"
                                    if [ -z "\$SONAR_BIN" ] && command -v pysonar >/dev/null 2>&1; then SONAR_BIN="\$(command -v pysonar)"; fi
                                    if [ -z "\$SONAR_BIN" ]; then echo "Neither sonar-scanner nor pysonar is available in the CI image."; exit 1; fi
                                    SONAR_ARGS="-Dsonar.host.url=https://sonarqube.home.siczb.de -Dsonar.token=\${SONAR_TOKEN} -Dsonar.projectKey=teltonika_rms -Dsonar.projectName=teltonika_rms -Dsonar.projectVersion=${env.VERSION}-${env.COMMIT_HASH} -Dsonar.python.version=3.14 -Dsonar.sources=custom_components/teltonika_rms -Dsonar.tests=tests"
                                    if [ -f "${env.SB_NAME}/sonar/tests/coverage.xml" ]; then SONAR_ARGS="\$SONAR_ARGS -Dsonar.python.coverage.reportPaths=${env.SB_NAME}/sonar/tests/coverage.xml"; fi
                                    if [ -f "${env.SB_NAME}/sonar/tests/pytest.xml" ]; then SONAR_ARGS="\$SONAR_ARGS -Dsonar.python.xunit.reportPath=${env.SB_NAME}/sonar/tests/pytest.xml"; fi
                                    "\$SONAR_BIN" \$SONAR_ARGS
                                """
                            }
                        }
                    } }
                }

                stage('Mutation Testing') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    options { timeout(time: 45, unit: 'MINUTES') }
                    steps { script { env.CURRENT_STAGE = 'Mutation Testing'; deleteDir(); unstash 'source'; sh """
                        mkdir -p ${env.SB_NAME}/mutation
                        python3 -m pytest --cov=custom_components/teltonika_rms --cov-context=test --cov-config=.coveragerc tests/
                        python3 -m mutmut run
                        python3 -m mutmut results > ${env.SB_NAME}/mutation/mutation-results.txt || true
                    """ } }
                    post { always { archiveArtifacts artifacts: "${env.SB_NAME}/mutation/**,mutants/.mutmut-cache/**", allowEmptyArchive: true } }
                }

                stage('Repository Rules') {
                    agent { docker { image "${env.CI_IMAGE}"; registryUrl "${env.CI_REGISTRY}"; registryCredentialsId 'harbor-jenkins-user'; label 'klymene' } }
                    steps { script { env.CURRENT_STAGE = 'Repository Rules'; deleteDir(); checkoutRepo(); sh '''
                        set -eu
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
                    ''' } }
                }

                stage('Hassfest') {
                    agent { label 'klymene' }
                    steps { script { env.CURRENT_STAGE = 'Hassfest'; deleteDir(); unstash 'source'; sh 'podman run --rm -v "$PWD:/github/workspace:z" ghcr.io/home-assistant/actions/hassfest:latest' } }
                }

                stage('OSV Scanner') {
                    agent { label 'klymene' }
                    steps { script { env.CURRENT_STAGE = 'OSV Scanner'; deleteDir(); unstash 'source'; sh 'podman run --rm -v "$PWD:/src:z" ghcr.io/google/osv-scanner:latest scan source -r --no-resolve /src' } }
                }

                stage('Actionlint') {
                    agent { label 'klymene' }
                    steps { script { env.CURRENT_STAGE = 'Actionlint'; deleteDir(); unstash 'source'; sh 'podman run --rm -v "$PWD:/repo:z" -w /repo docker.io/rhysd/actionlint:latest' } }
                }
            }
        }

        stage('Finalize Quality Gate Result') {
            agent { label 'klymene' }
            steps { script {
                env.CURRENT_STAGE = 'Finalize Quality Gate Result'
                normalizeWorkspacePermissions()
                deleteDir()
                ['qa-failure-marker-pytest-coverage','qa-failure-marker-ruff-lint','qa-failure-marker-ruff-format','qa-failure-marker-mypy','qa-failure-marker-translations','qa-failure-marker-pip-audit','qa-failure-marker-gitleaks','qa-failure-marker-trivy','qa-failure-marker-codeql'].each { unstashIfAvailable(it) }
                sh 'find .ci-failures -type f -print 2>/dev/null || true'
                def failedReports = sh(script: 'test -d .ci-failures && find .ci-failures -type f | wc -l || echo 0', returnStdout: true).trim()
                if (failedReports != '0') {
                    error('One or more report-producing QA stages failed. See .ci-failures markers and archived reports.')
                }
            } }
        }
    }

    post {
        always {
            script {
                def buildResult = currentBuild.currentResult ?: 'SUCCESS'
                def githubStatus = buildResult == 'ABORTED' ? 'FAILURE' : buildResult
                def checksConclusion = buildResult == 'SUCCESS' ? 'SUCCESS' : (buildResult == 'UNSTABLE' ? 'NEUTRAL' : 'FAILURE')
                def failedStage = buildResult == 'SUCCESS' ? '' : (env.CURRENT_STAGE ?: 'unknown')
                githubNotify(credentialsId: 'github token', status: githubStatus, context: 'Continuous Integration / Jenkins', description: failedStage ? "Build ${buildResult} in stage: ${failedStage}" : "Build ${buildResult}", account: env.GITHUB_OWNER, repo: env.GITHUB_REPO, sha: env.CAPTURED_SHA ?: 'main')
                publishChecks(name: 'Jenkins Build', title: 'Teltonika RMS Quality Gates', summary: failedStage ? "Status: ${buildResult}\nStage: ${failedStage}" : "Status: ${buildResult}", conclusion: checksConclusion, status: 'COMPLETED')
                node('klymene') {
                    normalizeWorkspacePermissions()
                    sh "podman rmi ${env.CI_IMAGE} || true"
                }
            }
        }
    }
}
