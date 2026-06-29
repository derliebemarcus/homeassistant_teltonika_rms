String sourceIncludes() {
    return 'CHANGELOG.md,CONTRIBUTING.md,custom_components/**,hacs.json,Jenkinsfile,jenkins/**,LICENSE,Makefile,osv-scanner.toml,pyproject.toml,pytest.ini,README.md,requirements-dev.in,requirements.txt,ROADMAP.md,tests/**,tools/**,.coveragerc,.flake8,.githooks/**,.github/**,.gitignore,.gitleaksignore,.trivyignore'
}

void initialize(def scmConfig, def execution) {
    stage('Initialize & Stash') {
        node('klymene') {
            execution.normalizeWorkspace()
            deleteDir()
            checkout scmConfig
            def checks = load 'jenkins/checks.groovy'
            checks.run('Initialize & Stash') { logFile ->
                env.CAPTURED_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                env.COMMIT_HASH = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                env.VERSION = sh(
                    script: '''python3 - <<'PY'
import json
from pathlib import Path
print(json.loads(Path("custom_components/teltonika_rms/manifest.json").read_text(encoding="utf-8"))["version"])
PY''',
                    returnStdout: true
                ).trim()
                execution.loggedShell("""
                    if grep -R "<<<<<<<\\|=======\\|>>>>>>>" requirements*.txt requirements*.in pyproject.toml custom_components tests tools 2>/dev/null; then
                        echo "Merge conflict markers detected."
                        exit 1
                    fi
                    echo "Commit: ${env.CAPTURED_SHA}"
                    echo "Version: ${env.VERSION}"
                """, logFile)
                stash name: 'source', includes: sourceIncludes(), useDefaultExcludes: false
            }
        }
    }
}

void buildCiEnvironment(def execution) {
    stage('Build CI Environment') {
        node('klymene') {
            execution.normalizeWorkspace()
            deleteDir()
            unstash 'source'
            def checks = load 'jenkins/checks.groovy'
            checks.run('Build CI Environment') { logFile ->
                execution.loggedShell("""cat <<'DOCKERFILE' > Dockerfile.ci
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
                withCredentials([
                    usernamePassword(
                        credentialsId: 'harbor-jenkins-user',
                        usernameVariable: 'U',
                        passwordVariable: 'P'
                    )
                ]) {
                    execution.loggedShell("""
                        podman login -u "\$U" -p "\$P" registry.home.siczb.de
                        podman push ${env.CI_IMAGE}
                    """, logFile)
                }
            }
        }
    }
}

void normalizeWorkspaces(def execution) {
    stage('Normalize Jenkins Workspaces') {
        node('klymene') {
            execution.normalizeWorkspace()
            deleteDir()
            unstash 'source'
            def checks = load 'jenkins/checks.groovy'
            checks.run('Normalize Jenkins Workspaces') { logFile ->
                execution.normalizeWorkspace(logFile)
            }
        }
    }
}

return this
