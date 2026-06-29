void runPipeline(def scmConfig, Map modules) {
    modules.setup.initialize(scmConfig, modules.execution)
    modules.setup.buildCiEnvironment(modules.execution)
    modules.setup.normalizeWorkspaces(modules.execution)

    stage('Parallel: Report-Producing QA') {
        def reportBranches = [:]
        reportBranches.putAll(modules.pythonReports.branches())
        reportBranches.putAll(modules.securityReports.branches(scmConfig))
        reportBranches.failFast = false
        parallel reportBranches
    }

    stage('Parallel: Blocking Gates') {
        def blockingBranches = [:]
        blockingBranches.sonarqube = modules.sonar.branch()
        blockingBranches.coveralls = modules.coveralls.branch()
        blockingBranches.mutation = modules.mutation.branch()
        blockingBranches.putAll(modules.repositoryGates.branches(scmConfig))
        blockingBranches.osv = modules.securityReports.osvGate(scmConfig)
        blockingBranches.failFast = false
        parallel blockingBranches
    }

    modules.finalQuality.runGate()
}

return this
