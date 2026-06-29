def bootstrap
def scmConfig = scm

node('klymene') {
    deleteDir()
    env.CAPTURED_SHA = ciCheckout(scmConfig)
    bootstrap = load 'jenkins/root.Jenkinsfile'
}

bootstrap.run(scmConfig)
