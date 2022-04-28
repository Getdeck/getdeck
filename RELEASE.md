# How to release a new version

1. Run in the root directory `poetry version <major, minor, patch>`
2. Run in the root directory `poetry run setversion`
3. Commit changes with message: "chore: bump version to <SemVer>"
4. Assign a g tag to the commit according to the semantic version that was just created (e.g. "0.6.15")
5. Push to GitHub (don't forget to push tags, too)
6. Draft a GitHub release based on the tag, auto-create the changelog
7. Publish the release

The rest should be automated