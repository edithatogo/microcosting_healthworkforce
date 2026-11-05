# Security policy

The maintained version is the current `main` branch. Update to its latest
qualified commit before reporting a defect; historical branches are unsupported.

Use GitHub's **Security → Report a vulnerability** private reporting form for
this repository. Private vulnerability reporting is enabled. Do not put secrets,
private workbooks, patient information or exploit credentials in public issues.
There is no guaranteed response deadline or dedicated security team.

Contributors must keep fixtures synthetic, preserve third-party licences, and
run `make all` before opening a pull request. Dependency updates use the hosted
Renovate app and the shared `github>edithatogo/renovate-config` preset; this
repository deliberately disables automatic merges for reviewed qualification.
GitHub secret scanning and push protection supplement local scanning.

CI uses read-only contents permission by default, pinned action commits, CodeQL,
dependency review and a redacted history secret scan. Coverage uploads use GitHub
OIDC rather than a stored Codecov token. Do not introduce privileged
`pull_request_target` execution of contributor code. Secrets are never needed
for local scientific tests. Changes to scientific assumptions require explicit
provenance and model review; passing software checks is not scientific approval.

Main protection must prevent deletion and force pushes and require the stable
hosted checks. No second human approval, CODEOWNERS gate or team gate is
required: this is a solo-maintainer repository. The repository administrator
retains a recovery bypass and must investigate failures before using it.
