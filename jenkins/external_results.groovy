def publishSarif(String sarifPath, String toolName = '') {
    ciUploadSarif(file: sarifPath, toolName: toolName)
}

def publishCoveralls(String coveragePath) {
    ciUploadCoveralls(file: coveragePath)
}

return this
