# Releases

Each of the four packages is released on its own, but one release can cover
any set of them.  A release goes through a pull request, and CI tags,
publishes and starts the next development versions.

## Versions

Each package keeps its version in `src/<name>/_version.py`, for example
`packages/qt-tools/src/qt_tools/_version.py`.  It is `X.Y` for a release and
`X.Y.dev0` between releases.  Wheel versions put the Qt or PyQt version first,
so qt-tools `1.4` built for Qt 6.12.1 is `qt6-tools` `6.12.1.1.4`, and
`1.5.dev0` is `6.12.1.1.5.dev0`.

A release of a package is tagged `<package>-vX.Y`, such as `qt-tools-v1.4`.
Other old tag forms, such as `pyqt-tools-v5.7.dev10` or
`qt-applications-v2.1-macOS`, are ignored.

The packages depend on each other in this order: qt-applications, qt-tools,
pyqt-plugins, pyqt-tools.  Each release is tested with the upstream wheels
built from the same commit, but users get the upstream packages from PyPI.  So
a package can only be released if every upstream package is either released
in the same commit or unchanged since its last release.  Its version file
doesn't count as a change.  For qt-applications and pyqt-plugins,
`.github/scripts/platform_tag.py` does count.

## Prepare a release

From a clean `main` checkout, with Git signing and `gh` working, name each
package and its new version:

```sh
mise run release qt-applications=2.4 qt-tools=1.4
```

The task:

1. Fetches `origin` with its tags and fast-forwards `main`.
2. Refuses a version that isn't newer than the package's current version and
   latest release tag, a tag or `release/...` branch that already exists, and
   an untagged release version of a package that isn't named.
3. Refuses a release that breaks the release order above.
4. Creates `release/qt-applications-v2.4+qt-tools-v1.4` with a signed commit
   that sets the versions, pushes it, and opens a pull request labelled
   `enqueue`.

Any failure stops the task without retrying.  Mergify merges the pull request
once its checks pass.

## What CI does

All of this is in `.github/workflows/ci.yml`, using `scripts/release.py`.

1. **Tag.**  When `all` passes on `main`, the `tag-release` job tags each
   package whose version is a release that has no tag yet.  It refuses if the
   run is no longer for the current `main`, never moves or replaces a tag, and
   checks the release order again.  It uses the `altendky-release` GitHub App
   (`RELEASE_APP_ID` and `RELEASE_APP_PRIVATE_KEY`), because tags created with
   `GITHUB_TOKEN` don't start workflow runs.
2. **Plan.**  Each tag starts a run, and its `release-plan` job decides what
   that run does.  The run for the most upstream package released at the
   commit publishes all of them.  The other tag runs skip everything after
   `release-plan`.  `tag-release` creates the most upstream tag last, so the
   other tags exist by the time its run starts, and `release-plan` checks that
   they do.
3. **Build and test.**  The publishing run builds every package without the
   cache, and tests them all, as on any other run.
4. **Publish.**  After `all` passes, the `publish` job checks each wheel's name
   and version and publishes the packages to PyPI in dependency order.  It uses
   trusted publishing through the `pypi` environment, whose required reviewer
   approves each release.
5. **GitHub Releases.**  The `github-release` job creates one release per tag,
   with the wheels published for that package.
6. **Post-release.**  The `post-release` job opens a
   `post-release/<tags>` pull request that moves each released package to its
   next `.dev0` version, such as `2.5.dev0` after `2.4`.  The App commits
   through the GitHub API so GitHub signs the commit, and the pull request is
   labelled `enqueue`.  Mergify approves and enqueues these pull requests.

A green `all` on a tag run doesn't mean the release is done; check the
`publish`, `github-release` and `post-release` jobs of the publishing run.

## Recover an interrupted release

Each step can be repeated without changing what an earlier attempt finished.

- **`tag-release` failed.**  Re-run the failed job.  Tags already at the
  commit are kept, and the missing ones are created.  If `main` has moved on,
  the job refuses to tag the old commit; instead, run the CI workflow on
  `main` (`gh workflow run ci.yml --ref main`), which tags the new `main` if
  the versions are still unreleased.
- **The publishing run says tags are missing.**  Some tags weren't created.
  Create them at the same commit, downstream packages first, with
  `tag-release` or by hand, then re-run the failed jobs.
- **`publish` failed partway.**  Re-run the failed jobs.  Wheels already on
  PyPI are skipped, and the `pypi` environment asks for approval again.
  Re-run failed jobs rather than the whole run, since a rebuild may not produce
  the same files.
- **`github-release` failed.**  Re-run it.  It creates missing releases,
  uploads missing wheels and publishes drafts, and stops if an existing wheel
  differs.
- **`post-release` failed.**  Re-run it.  It reuses its branch and pull
  request if they are its own, skips packages whose version on `main` has
  already moved on, and stops rather than change anything else.  Otherwise,
  bump the versions in a normal pull request.

Never move or delete a published tag.  If a release went out wrong, release a
new version.

## Test the release script

```sh
mise run release-test
```

The tests use temporary Git repositories and a fake GitHub, and CI runs them
in the repository checks.
