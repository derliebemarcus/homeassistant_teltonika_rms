@Library('jenkins-shared-library@main') _

ciHomeAssistantIntegration(
    scm: scm,
    agentLabel: 'klymene',
    mainBranch: 'main',
    weeklyMutationCron: 'H H * * 6',
    repository: [
        owner: 'derliebemarcus',
        name: 'homeassistant_teltonika_rms',
    ],
    componentPath: 'custom_components/teltonika_rms',
    manifestPath: 'custom_components/teltonika_rms/manifest.json',
    pythonVersion: '3.14',
    pythonCommand: 'python3',
    requirementsFile: 'requirements.txt',
    constraintsFile: '',
    testPaths: ['tests/unit', 'tests/ha'],
    coverageFloor: 97.1,
    reportRoot: 'build/reports',
    runtime: [
        mode: 'container',
        image: "registry.home.siczb.de/siczb/teltonika-rms-ci:${env.BUILD_NUMBER}",
        engine: 'podman',
        shell: '/bin/sh',
        pullPolicy: 'never',
        keepId: true,
        passEnvironment: [
            'CHANGE_TARGET',
            'GIT_PREVIOUS_SUCCESSFUL_COMMIT',
            'VERSION',
            'COMMIT_HASH',
        ],
    ],
    initializationRuntime: 'host',
    initializationCommand: '''
        cat <<'DOCKERFILE' > Dockerfile.ci
        FROM registry.home.siczb.de/siczb/python-ci:latest
        WORKDIR /build
        USER root
        RUN (apt-get update && apt-get install -y git curl ca-certificates) || (apk add --no-cache git curl ca-certificates) || true
        COPY requirements.txt ./
        RUN python3 -m pip install --upgrade pip --index-url https://artifacts.home.siczb.de/repository/pypi-proxy/simple/
        RUN python3 -m pip install --index-url https://artifacts.home.siczb.de/repository/pypi-proxy/simple/ -r requirements.txt
        COPY pyproject.toml pytest.ini .coveragerc ./
        COPY custom_components ./custom_components
        COPY tests ./tests
        COPY tools ./tools
        DOCKERFILE
        podman build --pull=never \
          -t "registry.home.siczb.de/siczb/teltonika-rms-ci:${BUILD_NUMBER}" \
          -f Dockerfile.ci .
    ''',
    cleanupCommand: '''
        podman rmi "registry.home.siczb.de/siczb/teltonika-rms-ci:${BUILD_NUMBER}" || true
    ''',
    workspaceNormalizationCommand: '''
        set +e
        [ -e "$WORKSPACE" ] || exit 0
        sudo chown -R "$(id -u):$(id -g)" "$WORKSPACE" || true
        sudo chmod -R u+rwX "$WORKSPACE" || true
    ''',
    prepareCommand: '',
    commands: [
        pytest: '''
            mkdir -p build/reports/pytest
            python3 -m pytest tests/unit tests/ha \
              --junitxml=build/reports/pytest/pytest.xml \
              --cov=. --cov-config=.coveragerc \
              --cov-report=xml:build/reports/pytest/coverage.xml \
              --cov-report=term-missing
        ''',
        ruffLint: '''
            mkdir -p build/reports/ruff
            python3 -m ruff check . --output-format=json \
              --output-file=build/reports/ruff/ruff-report.json
        ''',
        ruffFormat: '''
            mkdir -p build/reports/ruff-format
            python3 -m ruff format --check . \
              > build/reports/ruff-format/ruff-format.txt 2>&1
        ''',
        mypy: '''
            mkdir -p build/reports/mypy
            python3 -m mypy . --show-column-numbers \
              --junit-xml build/reports/mypy/mypy.xml
        ''',
        translations: '''
            mkdir -p build/reports/translations
            python3 tools/check_translations.py \
              > build/reports/translations/translations.txt 2>&1
        ''',
        pipAudit: '''
            mkdir -p build/reports/pip-audit
            python3 tools/run_pip_audit.py -r requirements.txt --format json \
              --output build/reports/pip-audit/pip-audit.json
        ''',
        mutation: '''
            mkdir -p build/reports/mutation
            python3 -m pytest --cov=custom_components/teltonika_rms \
              --cov-context=test --cov-config=.coveragerc tests/
            python3 -m mutmut run
            python3 -m mutmut results \
              > build/reports/mutation/mutation-results.txt || true
        ''',
        dependencyConsistency: 'tools/compile_lockfile.sh --check',
    ],
    mutation: [
        artifacts: 'build/reports/mutation/**,.mutmut-cache',
    ],
    hassfest: [enabled: true],
    sonar: [
        enabled: true,
        server: 'SonarQube',
        projectKey: 'teltonika_rms',
        projectName: 'teltonika_rms',
        timeoutMinutes: 15,
    ],
    coveralls: [
        enabled: true,
        file: 'build/reports/pytest/coverage.xml',
        credentialId: 'Coveralls',
        runtime: 'host',
    ],
    repositoryChecks: [
        commitMessageScript: 'tools/check_commit_messages.py',
        releaseNoteScript: 'tools/check_release_notes.py',
        changelog: 'CHANGELOG.md',
    ],
    security: [
        gitleaks: [enabled: true],
        trivy: [enabled: true],
        codeql: [
            enabled: true,
            toolName: 'codeql',
            toolPath: 'codeql',
            languages: ['python', 'actions'],
        ],
        osv: [enabled: true],
        actionlint: [enabled: true],
    ],
    sarifUploadScript: 'tools/upload_github_sarif.py',
    github: [
        credentialId: 'github token',
        publishStageChecks: true,
        publishFinalCheck: false,
        statusContext: 'Continuous Integration / Jenkins',
        title: 'Teltonika RMS Quality Gates',
    ],
    homeAssistant: [enabled: true],
)

def releaseStepName = ['ci', 'Change', 'sets', 'Release'].join('')
this.invokeMethod(releaseStepName, [[
    scm: scm,
    agentLabel: 'klymene',
    mainBranch: 'main',
    repository: [
        owner: 'derliebemarcus',
        name: 'homeassistant_teltonika_rms',
    ],
    packageFile: 'package.json',
    versionSyncCommand: 'npm run version:sync',
    autoMergePatch: true,
]] as Object[])
