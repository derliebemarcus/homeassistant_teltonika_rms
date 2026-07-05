# Continuous integration

The Jenkins pipeline classifies changed paths before entering any project or release stage.

When every changed path is explicitly allowed by the documentation-only policy, Jenkins publishes the normal required `Continuous Integration / Jenkins` status and exits successfully without running build, test, analysis, security, packaging, release, publication or deployment stages.

Mixed changes and changes with an unsafe comparison baseline always continue through the complete pipeline.
