@Library('jenkins-shared-library@main') _

ciRepositoryPipeline(
    profile: 'homeassistant-integration',
    repository: [
        provider: 'forgejo',
        owner: 'siczb',
        name: 'homeassistant_teltonika_rms',
    ],
    scmStatus: [
        context: 'Continuous Integration / Jenkins',
        title: 'Teltonika RMS Quality Gates',
        credentialId: 'forgejo',
        transport: 'api',
    ],
    features: [
        documentationOnly: [enabled: true],
        repositoryDocumentation: [enabled: true],
    ],
    profileConfig: [
        mainBranch: 'main',
        weeklyMutationCron: 'H H * * 6',
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
                set +e
                .ci-venv/bin/python tools/run_pip_audit.py \
                  -r requirements.txt --format json \
                  --output build/reports/pip-audit/pip-audit.json
                audit_status=$?
                set -e
                if [ "$audit_status" -ne 0 ]; then
                  cat build/reports/pip-audit/pip-audit.json
                fi
                exit "$audit_status"
            ''',
            osv: '''
                mkdir -p build/reports/osv
                scanner_status=0
                podman run --rm -v "$PWD:/src:z" \
                  ghcr.io/google/osv-scanner:latest scan source \
                  -r --no-resolve --format sarif /src \
                  > build/reports/osv/osv-scanner.sarif || scanner_status=$?
                test -s build/reports/osv/osv-scanner.sarif
                python3 -c "import json,sys; report=json.load(open(sys.argv[1], encoding='utf-8')); status=int(sys.argv[2]); results=[result for run in report.get('runs', []) for result in run.get('results', [])]; print('OSV Scanner remaining findings: %d' % len(results)); [print('%s | %s | %s' % (result.get('ruleId', '<unknown>'), result.get('message', {}).get('text', ''), next((location.get('physicalLocation', {}).get('artifactLocation', {}).get('uri', '') for location in result.get('locations', [])), ''))) for result in results]; raise SystemExit(status if status not in (0, 1) else (1 if results else 0))" \
                  build/reports/osv/osv-scanner.sarif "$scanner_status"
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
                    docker.io/rhysd/actionlint:latest -ignore forgejo "$workflow"
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
        homeAssistant: [enabled: true],
        release: [
            enabled: true,
            provider: 'forgejo',
            packageFile: 'package.json',
            versionSyncCommand: 'npm run version:sync',
            credentialId: 'forgejo',
            autoMergePatch: true,
        ],
    ],
)
