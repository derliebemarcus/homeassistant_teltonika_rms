@Library('jenkins-shared-library@main') _

ciRepositoryDocumentationContract(
    scm: scm,
    agentLabel: 'klymene',
)

if (ciDocumentationOnlyShortcut(
    scm: scm,
    agentLabel: 'klymene',
    repository: [
        owner: 'derliebemarcus',
        name: 'homeassistant_teltonika_rms',
    ],
    github: [
        credentialId: 'github token',
        statusContext: 'Continuous Integration / Jenkins',
        title: 'Teltonika RMS Quality Gates',
    ],
)) {
    return
}

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
    virtualEnvironment: '.ci-venv',
    pythonCommand: '.ci-venv/bin/python',
    requirementsFile: 'requirements.txt',
    constraintsFile: '',
    testPaths: ['tests/unit', 'tests/ha'],
    coverageFloor: 97.1,
    reportRoot: 'build/reports',
    commands: [
        pytest: '''
            mkdir -p build/reports/pytest
            .ci-venv/bin/python -m pytest tests/unit tests/ha \
              --junitxml=build/reports/pytest/pytest.xml \
              --cov=. --cov-config=.coveragerc \
              --cov-report=xml:build/reports/pytest/coverage.xml \
              --cov-report=term-missing
        ''',
        ruffLint: '''
            mkdir -p build/reports/ruff
            .ci-venv/bin/python -m ruff check . --output-format=json \
              --output-file=build/reports/ruff/ruff-report.json
        ''',
        ruffFormat: '''
            mkdir -p build/reports/ruff-format
            .ci-venv/bin/python -m ruff format --check . \
              > build/reports/ruff-format/ruff-format.txt 2>&1
        ''',
        mypy: '''
            mkdir -p build/reports/mypy
            .ci-venv/bin/python -m mypy . --show-column-numbers \
              --junit-xml build/reports/mypy/mypy.xml
        ''',
        translations: '''
            mkdir -p build/reports/translations
            .ci-venv/bin/python tools/check_translations.py \
              > build/reports/translations/translations.txt 2>&1
        ''',
        pipAudit: '''
            mkdir -p build/reports/pip-audit
            .ci-venv/bin/python tools/run_pip_audit.py \
              -r requirements.txt --format json \
              --output build/reports/pip-audit/pip-audit.json
        ''',
        trivy: 'bash tools/run_trivy.sh',
        mutation: '''
            mkdir -p build/reports/mutation
            .ci-venv/bin/python -m pytest \
              --cov=custom_components/teltonika_rms \
              --cov-context=test --cov-config=.coveragerc tests/
            .ci-venv/bin/python -m mutmut run
            .ci-venv/bin/python -m mutmut results \
              > build/reports/mutation/mutation-results.txt || true
        ''',
        dependencyConsistency: '''
            npm run check:ha-minimum
            PATH="$PWD/.ci-venv/bin:$PATH" tools/compile_lockfile.sh --check
        ''',
        actionlint: '''
            workflow_files="$(
              find .forgejo/workflows -type f -name '*.yml' -print
              find .forgejo/workflows -type f -name '*.yaml' -print
            )"
            test -n "$workflow_files"
            echo "$workflow_files" | while IFS= read -r workflow; do
              podman run --rm -v "$PWD:/repo:z" -w /repo \
                docker.io/rhysd/actionlint:latest "$workflow"
            done
        ''',
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
            languages: ['python'],
        ],
        osv: [enabled: true],
        actionlint: [enabled: true],
    ],
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
    credentialId: 'github token',
    autoMergePatch: true,
]] as Object[])
