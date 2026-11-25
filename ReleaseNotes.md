
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

To repair package assets on an existing tag, run the **Publish Package**
workflow manually and enter the tag name (for example, `v0.4.5`). The workflow
can update an existing release and replace its uploaded package files.
