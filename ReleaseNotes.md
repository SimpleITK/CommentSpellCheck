
# Release Process

Create an annotated tag for the release, then push it to the repository. For
example:

```sh
git tag -a v0.4.5 -m "Release v0.4.5"
git push upstream v0.4.5
```

Replace `upstream` with the name of the remote you push releases to. Pushing a
`v*` tag triggers the publish workflow, which creates a GitHub release titled
`Release v0.4.5` and generates its release notes.
