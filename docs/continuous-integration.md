# Continuous integration

The repository uses the central `homeassistant-integration` profile from
`jenkins-shared-library@main`. The Jenkinsfile contains only declarative repository and
profile configuration.

The profile uses `registry.home.siczb.de/siczb/homeassistant-integration-ci:3.14`, provided
by the maintenance repository. The image contains Python 3.14, Node.js 24, native-build
tooling, and the shared SonarQube client, but no Teltonika RMS source or dependencies.

During initialization, Jenkins creates `.ci-venv` once from the versioned
`requirements.txt`. The bootstrap stash distributes that virtual environment to the
following report and gate stages. Every Python command runs through
`.ci-venv/bin/python`. No project-specific image is built, pushed, or removed.

Stage groups run sequentially by default. Parallel execution requires an explicit profile
opt-in and is not enabled for this repository.

The dependency-consistency gate compiles the lockfile with the configured package index but
deliberately omits environment-specific index and trusted-host directives from the committed
`requirements.txt`.

The profile retains Pytest and coverage, Ruff lint and format, Mypy, translation validation,
Pip Audit, mutation testing, Hassfest, SonarQube, Coveralls, Gitleaks, Trivy, CodeQL, OSV,
Actionlint, repository rules, and dependency consistency. CodeQL scans Python; Forgejo
workflow files are validated separately with Actionlint in Forgejo compatibility mode.
Mutation testing runs for pull requests and `main`; `main` retains the weekly `H H * * 6`
run.

Forgejo is the authoritative SCM, commit-status, and release provider. GitHub-specific
repository metadata and status credentials are not part of the Jenkins lifecycle.

The documentation-only shortcut remains active. Mixed changes and changes with an unsafe
comparison baseline always continue through the complete pipeline. Repository documentation
is validated through the central documentation contract.
