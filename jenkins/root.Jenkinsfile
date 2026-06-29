void run(def scmConfig) {
    def pipelineScript
    def modules = [:]

    node('klymene') {
        deleteDir()
        ciCheckout(scmConfig)
        pipelineScript = load 'jenkins/pipeline.groovy'
        modules.setup = load 'jenkins/setup_stages.groovy'
        modules.pythonReports = load 'jenkins/python_reports.groovy'
        modules.securityReports = load 'jenkins/security_reports.groovy'
        modules.sonar = load 'jenkins/sonar_gate.groovy'
        modules.coveralls = load 'jenkins/coveralls_gate.groovy'
        modules.mutation = load 'jenkins/mutation_gate.groovy'
        modules.repositoryGates = load 'jenkins/repository_gates.groovy'
        modules.finalQuality = load 'jenkins/final_quality_gate.groovy'
        modules.execution = load 'jenkins/execution.groovy'
    }

    if (env.BRANCH_NAME == 'main') {
        properties([
            disableConcurrentBuilds(),
            pipelineTriggers([cron('H H * * 6')])
        ])
    } else {
        properties([disableConcurrentBuilds()])
    }

    env.CI_BASE_IMAGE = 'registry.home.siczb.de/siczb/python-ci:latest'
    env.CI_IMAGE = "registry.home.siczb.de/siczb/teltonika-rms-ci:${env.BUILD_NUMBER}"
    env.CI_REGISTRY = 'https://registry.home.siczb.de'
    env.PYPI_URL = 'https://artifacts.home.siczb.de/repository/pypi-proxy/simple/'
    env.GITHUB_OWNER = 'derliebemarcus'
    env.GITHUB_REPO = 'homeassistant_teltonika_rms'
    env.SB_NAME = "build_sb_${env.BUILD_NUMBER}"
    env.CAPTURED_SHA = env.CAPTURED_SHA ?: ''
    env.COMMIT_HASH = ''
    env.VERSION = ''
    env.CI_FAILED_STAGE = ''

    try {
        pipelineScript.runPipeline(scmConfig, modules)
    } catch (err) {
        currentBuild.result = currentBuild.currentResult == 'ABORTED' ? 'ABORTED' : 'FAILURE'
        throw err
    } finally {
        try {
            ciPublishGitHubStatus([title: 'Teltonika RMS Quality Gates'])
        } finally {
            try {
                ciNotifyHomeAssistant()
            } finally {
                node('klymene') {
                    modules.execution.normalizeWorkspace()
                    sh "podman rmi ${env.CI_IMAGE} || true"
                }
            }
        }
    }
}

return this
