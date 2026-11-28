"""Tests for scripts/release.py.  Run with `mise run release-test`."""

import base64
import contextlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import release  # noqa: E402
from release import PACKAGES, Release, ReleaseError  # noqa: E402


class VersionTests(unittest.TestCase):
    def test_order(self):
        ordered = ["1.3", "1.4.dev0", "1.4.dev1", "1.4", "1.4.1.dev0", "1.4.1", "1.5.dev0", "2"]
        keys = [release.parse_version(version) for version in ordered]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(len(set(keys)), len(keys))

    def test_trailing_zeros_are_equal(self):
        self.assertEqual(release.parse_version("2.4"), release.parse_version("2.4.0"))

    def test_invalid(self):
        for value in ["", "v1.4", "1.04", "1.4rc1", "1.4.post1", "1.4+local", "1..4", "1.4.dev", "1.4.dev01"]:
            with self.subTest(value=value), self.assertRaises(ReleaseError):
                release.parse_version(value)

    def test_final(self):
        self.assertTrue(release.is_final("2.4"))
        self.assertFalse(release.is_final("2.4.dev0"))
        self.assertEqual(release.final_version("2.4"), "2.4")
        with self.assertRaises(ReleaseError):
            release.final_version("2.4.dev0")

    def test_next_dev(self):
        self.assertEqual(release.next_dev("2.4"), "2.5.dev0")
        self.assertEqual(release.next_dev("1.0.1"), "1.0.2.dev0")
        self.assertEqual(release.next_dev("4"), "5.dev0")
        with self.assertRaises(ReleaseError):
            release.next_dev("2.5.dev0")

    def test_version_file(self):
        text = '# A comment.\n__version__ = "2.4.dev0"\n'
        self.assertEqual(release.read_version_text(text, "file"), "2.4.dev0")
        self.assertEqual(
            release.replace_version_text(text, "2.4", "file"), '# A comment.\n__version__ = "2.4"\n',
        )
        for bad in ["", '__version__ = "1"\n__version__ = "2"\n', '__version__ = "x"\n']:
            with self.subTest(bad=bad), self.assertRaises(ReleaseError):
                release.read_version_text(bad, "file")

    def test_repository_version_files(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        for package in PACKAGES:
            with self.subTest(package=package):
                text = (root / release.version_path(package)).read_text()
                release.read_version_text(text, package)

    def test_parse_tag(self):
        self.assertEqual(release.parse_tag("qt-tools-v1.4"), ("qt-tools", "1.4"))
        self.assertEqual(release.parse_tag("pyqt-tools-v3.3"), ("pyqt-tools", "3.3"))
        self.assertEqual(release.parse_tag("qt-applications-v2"), ("qt-applications", "2"))
        for tag in ["pyqt-tools-v5.7.dev10", "qt-applications-v2.1-macOS", "qt-tools-v1.0.1-5.15.2",
                    "pyqt-tools-v1.4rc0", "v3.3", "other-v1.0"]:
            with self.subTest(tag=tag):
                self.assertIsNone(release.parse_tag(tag))

    def test_latest_release_tag_ignores_other_forms(self):
        tags = {"pyqt-tools-v3.3": "a", "pyqt-tools-v5.7.dev10": "b", "pyqt-tools-v3.0.3": "c", "qt-tools-v9": "d"}
        self.assertEqual(release.latest_release_tag(tags, "pyqt-tools"), "pyqt-tools-v3.3")
        self.assertIsNone(release.latest_release_tag(tags, "pyqt-plugins"))

    def test_releases_from_environment(self):
        items = [Release("qt-tools", "1.4").to_json(), Release("pyqt-tools", "4.0").to_json()]
        self.assertEqual(
            release.releases_from_environment({"RELEASES": json.dumps(items)}),
            [Release("qt-tools", "1.4"), Release("pyqt-tools", "4.0")],
        )
        for bad in [[], items[::-1], [items[0], items[0]], [{**items[0], "tag": "qt-tools-v9"}],
                    [{"package": "qt-tools", "version": "1.4.dev0", "tag": "qt-tools-v1.4.dev0"}]]:
            with self.subTest(bad=bad), self.assertRaises(ReleaseError):
                release.releases_from_environment({"RELEASES": json.dumps(bad)})


class GitTestCase(unittest.TestCase):
    """A repository with the four packages, isolated from the user's Git setup."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = pathlib.Path(directory.name) / "repository"
        self.root.mkdir()
        config = pathlib.Path(directory.name) / "gitconfig"
        config.write_text("")
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update({
            "GIT_CONFIG_GLOBAL": str(config),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        })
        self.enterContext(mock.patch.dict(os.environ, environment, clear=True))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.git("init", "--quiet", "--initial-branch=main")
        for package in PACKAGES:
            self.write(f"packages/{package}/setup.py", f"# {package}\n")
            self.set_version(package, "1.0.dev0")
        self.write(".github/scripts/platform_tag.py", "# platform tags\n")
        self.write(".github/ci-config.json", "{}\n")
        self.commit("Initial")

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, text=True, capture_output=True,
        ).stdout.strip()

    def write(self, path, text):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def set_version(self, package, version):
        self.write(release.version_path(package), f'# Version.\n__version__ = "{version}"\n')

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "--message", message)
        return self.git("rev-parse", "HEAD")

    def release_all(self, version="1.0"):
        """Commit a release of every package and tag it."""
        for package in PACKAGES:
            self.set_version(package, version)
        sha = self.commit(f"Release {version}")
        for package in PACKAGES:
            self.git("tag", f"{package}-v{version}")
        return sha

    def tags(self):
        return release.local_tags(self.root)


class ReleaseOrderTests(GitTestCase):
    def setUp(self):
        super().setUp()
        self.release_all("1.0")
        for package in PACKAGES:
            self.set_version(package, "1.1.dev0")
        self.head = self.commit("Start development")

    def check(self, releasing):
        release.check_release_order(self.root, self.tags(), self.git("rev-parse", "HEAD"), set(releasing))

    def test_unchanged_upstream_allows_downstream(self):
        self.check({"pyqt-tools"})

    def test_upstream_change_refuses_downstream(self):
        self.write("packages/qt-tools/setup.py", "# changed\n")
        self.commit("Change qt-tools")
        with self.assertRaisesRegex(ReleaseError, "pyqt-tools needs qt-tools, which changed since qt-tools-v1.0"):
            self.check({"pyqt-tools"})
        with self.assertRaisesRegex(ReleaseError, "pyqt-plugins needs qt-tools"):
            self.check({"pyqt-plugins"})
        self.check({"qt-applications"})
        self.check({"qt-tools"})
        self.check({"qt-tools", "pyqt-tools"})

    def test_transitive_upstream(self):
        self.write("packages/qt-applications/setup.py", "# changed\n")
        self.commit("Change qt-applications")
        with self.assertRaisesRegex(ReleaseError, "pyqt-tools needs qt-applications"):
            self.check({"qt-tools", "pyqt-plugins", "pyqt-tools"})
        self.check(PACKAGES)

    def test_version_file_changes_are_ignored(self):
        self.set_version("qt-tools", "2.0.dev0")
        self.commit("Plan a major qt-tools release")
        self.check({"pyqt-tools"})

    def test_extra_sources(self):
        self.write(".github/scripts/platform_tag.py", "# changed\n")
        self.commit("Change platform tags")
        with self.assertRaisesRegex(ReleaseError, "pyqt-tools needs qt-applications.*\n.*pyqt-tools needs pyqt-plugins"):
            self.check({"pyqt-tools"})
        with self.assertRaisesRegex(ReleaseError, "qt-tools needs qt-applications"):
            self.check({"qt-tools"})

    def test_ci_config(self):
        self.write(".github/ci-config.json", '{"qt": "changed"}\n')
        self.commit("Change Qt")
        with self.assertRaisesRegex(ReleaseError, "pyqt-tools needs qt-applications"):
            self.check({"pyqt-tools"})
        self.check(PACKAGES)

    def test_unreleased_upstream(self):
        self.git("tag", "--delete", "qt-applications-v1.0")
        self.git("tag", "qt-applications-v0.9.dev1", "HEAD~1")
        with self.assertRaisesRegex(ReleaseError, "qt-applications, which has no release tag"):
            self.check({"qt-tools"})

    def test_uses_the_latest_release_in_history(self):
        self.write("packages/qt-tools/setup.py", "# changed\n")
        self.set_version("qt-tools", "1.1")
        self.commit("Release qt-tools 1.1")
        self.git("tag", "qt-tools-v1.1")
        # A higher tag outside this history doesn't count.
        self.git("switch", "--quiet", "--create", "side", self.head)
        self.write("packages/qt-tools/other.py", "")
        self.git("tag", "qt-tools-v1.2", self.commit("Side"))
        self.git("switch", "--quiet", "main")
        self.check({"pyqt-tools"})


class PendingReleaseTests(GitTestCase):
    def test_pending(self):
        old = self.release_all("1.0")
        self.set_version("qt-tools", "1.1")
        head = self.commit("Release qt-tools 1.1")
        # Everything else is still at the tagged 1.0 until post-release merges.
        self.assertEqual(release.pending_releases(self.root, self.tags(), head), [Release("qt-tools", "1.1")])
        self.git("tag", "qt-tools-v1.1")
        self.assertEqual(release.pending_releases(self.root, self.tags(), head), [Release("qt-tools", "1.1")])
        # The earlier release commit still has its own tags.
        self.assertEqual(
            release.pending_releases(self.root, self.tags(), old), [Release(package, "1.0") for package in PACKAGES],
        )

    def test_development_versions_are_not_releases(self):
        self.assertEqual(release.pending_releases(self.root, self.tags(), self.git("rev-parse", "HEAD")), [])


def environment(tag, sha, event="push"):
    return {
        "GITHUB_EVENT_NAME": event,
        "GITHUB_REF_TYPE": "tag",
        "GITHUB_REF_NAME": tag,
        "GITHUB_REF": f"refs/tags/{tag}",
        "GITHUB_SHA": sha,
    }


class PlanTests(GitTestCase):
    def setUp(self):
        super().setUp()
        self.release_all("1.0")
        for package in PACKAGES:
            self.set_version(package, "1.1.dev0")
        self.commit("Start development")
        self.write("packages/qt-tools/setup.py", "# changed\n")
        self.set_version("qt-tools", "1.1")
        self.set_version("pyqt-tools", "1.1")
        self.head = self.commit("Release qt-tools and pyqt-tools")

    def plan(self, tag):
        self.git("checkout", "--quiet", "--detach", tag)
        return release.plan(self.root, environment(tag, self.head))

    def test_branch_and_pull_request_runs_build(self):
        expected = {"build": "true", "publish": "false", "packages": "[]", "releases": "[]"}
        self.assertEqual(release.plan(self.root, {"GITHUB_EVENT_NAME": "pull_request"}), expected)
        self.assertEqual(release.plan(self.root, {"GITHUB_EVENT_NAME": "push", "GITHUB_REF_TYPE": "branch"}), expected)
        self.assertEqual(
            release.plan(self.root, {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF_TYPE": "tag"}), expected,
        )

    def test_downstream_tag_run_defers_to_the_upstream_one(self):
        # Created first by tag-release, before the qt-tools tag exists.
        self.git("tag", "pyqt-tools-v1.1")
        self.assertEqual(self.plan("pyqt-tools-v1.1")["build"], "false")
        self.git("tag", "qt-tools-v1.1")
        self.assertEqual(self.plan("pyqt-tools-v1.1")["build"], "false")
        outputs = self.plan("qt-tools-v1.1")
        self.assertEqual(outputs["build"], "true")
        self.assertEqual(outputs["publish"], "true")
        self.assertEqual(json.loads(outputs["packages"]), ["qt-tools", "pyqt-tools"])
        self.assertEqual(
            json.loads(outputs["releases"]),
            [Release("qt-tools", "1.1").to_json(), Release("pyqt-tools", "1.1").to_json()],
        )

    def test_publishing_run_needs_every_tag(self):
        self.git("tag", "qt-tools-v1.1")
        with self.assertRaisesRegex(ReleaseError, "Tags missing .*: pyqt-tools-v1.1"):
            self.plan("qt-tools-v1.1")

    def test_tag_must_match_version(self):
        self.git("tag", "qt-applications-v1.1")
        with self.assertRaisesRegex(ReleaseError, "does not match"):
            self.plan("qt-applications-v1.1")

    def test_not_a_release_tag(self):
        with self.assertRaisesRegex(ReleaseError, "not a release tag"):
            release.plan(self.root, environment("qt-tools-v1.1-5.15.2", self.head))

    def test_release_order(self):
        self.set_version("qt-tools", "1.1.dev0")
        self.head = self.commit("Only release pyqt-tools")
        self.git("tag", "pyqt-tools-v1.1")
        with self.assertRaisesRegex(ReleaseError, "pyqt-tools needs qt-tools"):
            self.plan("pyqt-tools-v1.1")


class FakeGitHub:
    repository = "altendky/pyqt-tools"

    def __init__(self, root, refs):
        self.root = root
        self.refs = dict(refs)
        self.created = []
        self.pulls = []
        self.commits = {}
        self.calls = []

    def ref(self, name):
        return self.refs.get(name)

    def create_ref(self, name, sha):
        if name in self.refs:
            raise ReleaseError(f"{name} exists")
        self.refs[name] = sha
        self.created.append(name)

    def fast_forward(self, name, sha):
        self.refs[name] = sha

    def contains(self, ancestor, descendant):
        # Commits made through the fake API exist only here, never on main.
        return ancestor not in self.commits and release.is_ancestor(self.root, ancestor, descendant)

    def contents(self, path, ref):
        if ref in self.commits:
            return self.commits[ref]["files"][path]
        return subprocess.run(
            ["git", "show", f"{ref}:{path}"], cwd=self.root, check=True, text=True, capture_output=True,
        ).stdout

    def graphql(self, payload):
        change = payload["variables"]["input"]
        branch = "heads/" + change["branch"]["branchName"]
        self.assertion(self.refs[branch] == change["expectedHeadOid"])
        sha = f"commit{len(self.commits)}"
        self.commits[sha] = {
            "message": change["message"]["headline"],
            "parent": change["expectedHeadOid"],
            "files": {
                item["path"]: base64.b64decode(item["contents"]).decode()
                for item in change["fileChanges"]["additions"]
            },
        }
        self.refs[branch] = sha
        return {"createCommitOnBranch": {"commit": {"oid": sha}}}

    def assertion(self, condition):
        if not condition:
            raise AssertionError("unexpected fake GitHub state")

    def api(self, endpoint, *, method="GET", data=None, missing_ok=False):
        self.calls.append((method, endpoint, data))
        if endpoint.startswith("git/commits/"):
            commit = self.commits[endpoint.removeprefix("git/commits/")]
            return {
                "message": commit["message"],
                "parents": [{"sha": commit["parent"]}],
                "verification": {"verified": True},
            }
        if endpoint.startswith("compare/"):
            head = endpoint.split("...")[1]
            return {"files": [{"filename": path} for path in self.commits[head]["files"]]}
        if endpoint.startswith("pulls?"):
            return self.pulls
        if endpoint.startswith("issues/"):
            return None
        raise AssertionError(f"unexpected API call {method} {endpoint}")

    def gh(self, *args, input_text=None):
        self.calls.append(("gh", *args))
        if args[:2] == ("pr", "create"):
            return "https://github.com/altendky/pyqt-tools/pull/1\n"
        return ""


class TagTests(GitTestCase):
    def setUp(self):
        super().setUp()
        self.release_all("1.0")
        self.set_version("qt-applications", "1.1")
        self.set_version("pyqt-plugins", "1.1")
        self.set_version("pyqt-tools", "1.1")
        self.head = self.commit("Release")
        self.environ = {"GITHUB_REF": "refs/heads/main", "GITHUB_SHA": self.head}

    def test_tags_downstream_first(self):
        github = FakeGitHub(self.root, {"heads/main": self.head})
        releases = release.tag_releases(self.root, github, self.environ)
        self.assertEqual([r.package for r in releases], ["qt-applications", "pyqt-plugins", "pyqt-tools"])
        self.assertEqual(github.created, ["tags/pyqt-tools-v1.1", "tags/pyqt-plugins-v1.1", "tags/qt-applications-v1.1"])
        self.assertEqual({github.refs[name] for name in github.created}, {self.head})

    def test_rerun_creates_only_missing_tags(self):
        github = FakeGitHub(self.root, {"heads/main": self.head, "tags/pyqt-tools-v1.1": self.head})
        release.tag_releases(self.root, github, self.environ)
        self.assertEqual(github.created, ["tags/pyqt-plugins-v1.1", "tags/qt-applications-v1.1"])

    def test_refuses_stale_main(self):
        github = FakeGitHub(self.root, {"heads/main": "newer"})
        with self.assertRaisesRegex(ReleaseError, "stale"):
            release.tag_releases(self.root, github, self.environ)
        self.assertEqual(github.created, [])

    def test_finishes_a_started_batch_after_main_moves(self):
        github = FakeGitHub(self.root, {"heads/main": "newer", "tags/pyqt-tools-v1.1": self.head})
        release.tag_releases(self.root, github, self.environ)
        self.assertEqual(github.created, ["tags/pyqt-plugins-v1.1", "tags/qt-applications-v1.1"])

    def test_refuses_while_an_earlier_batch_is_incomplete(self):
        self.git("tag", "pyqt-tools-v1.1")
        self.write("README", "later\n")
        self.environ["GITHUB_SHA"] = later = self.commit("Later")
        github = FakeGitHub(self.root, {"heads/main": later, "tags/pyqt-tools-v1.1": self.head})
        with self.assertRaisesRegex(ReleaseError, f"pyqt-tools-v1.1 at {self.head} still need"):
            release.tag_releases(self.root, github, self.environ)
        self.assertEqual(github.created, [])
        # Finishing the earlier commit's tags lets later commits tag again.
        self.git("tag", "pyqt-plugins-v1.1", self.head)
        self.git("tag", "qt-applications-v1.1", self.head)
        self.assertEqual(release.tag_releases(self.root, github, self.environ), [])

    def test_never_replaces_a_tag(self):
        github = FakeGitHub(self.root, {"heads/main": self.head, "tags/pyqt-tools-v1.1": "elsewhere"})
        with self.assertRaisesRegex(ReleaseError, "leaving it unchanged"):
            release.tag_releases(self.root, github, self.environ)
        self.assertEqual(github.created, [])

    def test_release_order(self):
        self.set_version("qt-applications", "1.1.dev0")
        self.write("packages/qt-applications/setup.py", "# changed\n")
        self.environ["GITHUB_SHA"] = head = self.commit("Change qt-applications")
        github = FakeGitHub(self.root, {"heads/main": head})
        with self.assertRaisesRegex(ReleaseError, "pyqt-plugins needs qt-applications"):
            release.tag_releases(self.root, github, self.environ)
        self.assertEqual(github.created, [])

    def test_nothing_to_tag(self):
        self.git("tag", "qt-applications-v1.1", "HEAD~1")
        self.git("tag", "pyqt-plugins-v1.1", "HEAD~1")
        self.git("tag", "pyqt-tools-v1.1", "HEAD~1")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(release.tag_releases(self.root, FakeGitHub(self.root, {"heads/main": self.head}), self.environ), [])

    def test_requires_main(self):
        with self.assertRaisesRegex(ReleaseError, "main run"):
            release.tag_releases(self.root, FakeGitHub(self.root, {}), {"GITHUB_REF": "refs/heads/other"})


class PostReleaseTests(GitTestCase):
    def setUp(self):
        super().setUp()
        self.set_version("qt-tools", "1.4")
        self.set_version("pyqt-tools", "4.0")
        self.main = self.commit("Release")
        self.releases = [Release("qt-tools", "1.4"), Release("pyqt-tools", "4.0")]

    def test_opens_pull_request(self):
        github = FakeGitHub(self.root, {"heads/main": self.main})
        url = release.post_release(self.root, github, self.releases)
        self.assertEqual(url, "https://github.com/altendky/pyqt-tools/pull/1")
        branch = "heads/post-release/qt-tools-v1.4+pyqt-tools-v4.0"
        commit = github.commits[github.refs[branch]]
        self.assertEqual(commit["parent"], self.main)
        self.assertEqual(commit["message"], "Start qt-tools 1.5.dev0 and pyqt-tools 4.1.dev0 development")
        self.assertEqual(
            {path: release.read_version_text(text, path) for path, text in commit["files"].items()},
            {release.version_path("qt-tools"): "1.5.dev0", release.version_path("pyqt-tools"): "4.1.dev0"},
        )
        [create] = [call for call in github.calls if call[:3] == ("gh", "pr", "create")]
        self.assertIn("enqueue", create)

    def test_skips_packages_main_moved_past(self):
        self.set_version("pyqt-tools", "4.1.dev0")
        github = FakeGitHub(self.root, {"heads/main": self.commit("Bumped by hand")})
        release.post_release(self.root, github, self.releases)
        [commit] = github.commits.values()
        self.assertEqual(list(commit["files"]), [release.version_path("qt-tools")])

    def test_nothing_to_do(self):
        for package in PACKAGES:
            self.set_version(package, "9.dev0")
        github = FakeGitHub(self.root, {"heads/main": self.commit("Moved on")})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(release.post_release(self.root, github, self.releases))
        self.assertEqual(github.created, [])

    def test_completes_an_empty_branch_from_an_earlier_attempt(self):
        branch = "heads/post-release/qt-tools-v1.4+pyqt-tools-v4.0"
        newer = self.commit("Unrelated")
        github = FakeGitHub(self.root, {"heads/main": newer, branch: self.main})
        release.post_release(self.root, github, self.releases)
        self.assertEqual(github.commits[github.refs[branch]]["parent"], newer)

    def test_reuses_an_open_pull_request(self):
        github = FakeGitHub(self.root, {"heads/main": self.main})
        release.post_release(self.root, github, self.releases)
        sha = github.refs["heads/post-release/qt-tools-v1.4+pyqt-tools-v4.0"]
        github.pulls = [{"state": "open", "head": {"sha": sha}, "labels": [], "number": 5, "html_url": "url"}]
        self.assertEqual(release.post_release(self.root, github, self.releases), "url")
        self.assertEqual(len(github.commits), 1)
        self.assertIn(("POST", "issues/5/labels", {"labels": ["enqueue"]}), github.calls)

    def test_refuses_a_closed_pull_request(self):
        github = FakeGitHub(self.root, {"heads/main": self.main})
        github.pulls = [{"state": "closed", "html_url": "url"}]
        with self.assertRaisesRegex(ReleaseError, "closed"):
            release.post_release(self.root, github, self.releases)


class CollectTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.artifacts = pathlib.Path(directory.name) / "artifacts"
        self.dist = pathlib.Path(directory.name) / "dist"

    def wheel(self, package, artifact, name, content=b"wheel"):
        path = self.artifacts / package / artifact / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def collect(self, *releases):
        with contextlib.redirect_stdout(io.StringIO()):
            release.collect(list(releases), self.artifacts, self.dist)

    def test_collect(self):
        self.wheel("qt-tools", "qt-tools-qt5.15.2", "qt5_tools-5.15.2.1.4-py3-none-any.whl")
        self.wheel("qt-tools", "qt-tools-qt6.12.1", "qt6_tools-6.12.1.1.4-py3-none-any.whl")
        self.wheel("pyqt-plugins", "a", "pyqt6_plugins-6.12.1.2.4-cp313-cp313-win_amd64.whl")
        self.collect(Release("qt-tools", "1.4"), Release("pyqt-plugins", "2.4"))
        self.assertEqual(
            sorted(path.relative_to(self.dist).as_posix() for path in self.dist.rglob("*.whl")),
            [
                "pyqt-plugins/pyqt6_plugins-6.12.1.2.4-cp313-cp313-win_amd64.whl",
                "qt-tools/qt5_tools-5.15.2.1.4-py3-none-any.whl",
                "qt-tools/qt6_tools-6.12.1.1.4-py3-none-any.whl",
            ],
        )

    def test_wrong_version(self):
        self.wheel("qt-tools", "a", "qt6_tools-6.12.1.1.4.dev0-py3-none-any.whl")
        with self.assertRaisesRegex(ReleaseError, "does not have version"):
            self.collect(Release("qt-tools", "1.4"))

    def test_wrong_package(self):
        self.wheel("qt-tools", "a", "pyqt6_tools-6.12.1.1.4-py3-none-any.whl")
        with self.assertRaisesRegex(ReleaseError, "is not a qt-tools wheel"):
            self.collect(Release("qt-tools", "1.4"))

    def test_no_wheels(self):
        with self.assertRaisesRegex(ReleaseError, "No wheels"):
            self.collect(Release("qt-tools", "1.4"))

    def test_identical_duplicates(self):
        name = "qt6_applications-6.12.1.2.4-py3-none-macosx_14_0_universal2.whl"
        self.wheel("qt-applications", "a", name)
        self.wheel("qt-applications", "b", name)
        self.collect(Release("qt-applications", "2.4"))

    def test_different_duplicates(self):
        name = "qt6_applications-6.12.1.2.4-py3-none-macosx_14_0_universal2.whl"
        self.wheel("qt-applications", "a", name, b"one")
        self.wheel("qt-applications", "b", name, b"two")
        with self.assertRaisesRegex(ReleaseError, "Different wheels share the name"):
            self.collect(Release("qt-applications", "2.4"))


class GitHubReleaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dist = pathlib.Path(directory.name)
        self.wheel = self.dist / "qt-tools" / "qt6_tools-6.12.1.1.4-py3-none-any.whl"
        self.wheel.parent.mkdir()
        self.wheel.write_bytes(b"wheel")
        self.release = Release("qt-tools", "1.4")

    def run_releases(self, existing):
        github = FakeGitHub(None, {})
        with mock.patch.object(release, "find_release", return_value=existing), \
                contextlib.redirect_stdout(io.StringIO()):
            release.github_releases(github, [self.release], self.dist)
        return [call[1:3] for call in github.calls]

    def test_create(self):
        self.assertEqual(self.run_releases(None), [("release", "create")])

    def test_complete_a_draft(self):
        calls = self.run_releases({"draft": True, "assets": []})
        self.assertEqual(calls, [("release", "upload"), ("release", "edit")])

    def test_complete(self):
        asset = {"name": self.wheel.name, "size": 5, "digest": release.sha256(self.wheel)}
        self.assertEqual(self.run_releases({"draft": False, "assets": [asset]}), [])

    def test_different_asset(self):
        asset = {"name": self.wheel.name, "size": 5, "digest": "sha256:other"}
        with self.assertRaisesRegex(ReleaseError, "different"):
            self.run_releases({"draft": False, "assets": [asset]})

    def test_notes(self):
        notes = release.release_notes(self.release, [self.wheel, self.wheel])
        self.assertEqual(
            notes,
            "qt-tools 1.4, published to PyPI as:\n\n"
            "- [qt6-tools 6.12.1.1.4](https://pypi.org/project/qt6-tools/6.12.1.1.4/)\n",
        )


class PrepareTests(GitTestCase):
    """Prepare against a local origin, faking only GitHub and commit signing."""

    def setUp(self):
        super().setUp()
        self.release_all("1.0")
        for package in PACKAGES:
            self.set_version(package, "1.1.dev0")
        self.commit("Start development")
        self.origin = self.root.parent / "origin.git"
        subprocess.run(["git", "clone", "--quiet", "--bare", str(self.root), str(self.origin)], check=True)
        self.git("remote", "add", "origin", str(self.origin))
        self.git("fetch", "--quiet", "origin")
        self.commands = []

    def runner(self, root, *command):
        self.commands.append(command)
        if command == ("git", "remote", "get-url", "origin"):
            return "git@github.com:altendky/pyqt-tools.git"
        if command[0] == "gh":
            return "https://github.com/altendky/pyqt-tools/pull/2"
        if command[:2] == ("git", "commit"):
            # The test repository has no signing key.
            command = tuple(part for part in command if part != "--gpg-sign")
        result = subprocess.run(command, cwd=root, text=True, capture_output=True)
        if result.returncode:
            raise ReleaseError(f"{command} failed: {result.stderr}")
        return result.stdout.strip()

    def prepare(self, *specs):
        return release.prepare(self.root, list(specs), runner=self.runner)

    def test_prepare(self):
        # Someone else pushed to main in the meantime.
        other = self.root.parent / "other"
        subprocess.run(["git", "clone", "--quiet", str(self.origin), str(other)], check=True)
        (other / "README").write_text("new\n")
        subprocess.run(["git", "add", "README"], cwd=other, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "Other"], cwd=other, check=True)
        subprocess.run(["git", "push", "--quiet", "origin", "main"], cwd=other, check=True)

        url = self.prepare("qt-tools=1.1", "qt-applications=1.1")
        self.assertEqual(url, "https://github.com/altendky/pyqt-tools/pull/2")
        branch = "release/qt-applications-v1.1+qt-tools-v1.1"
        self.assertEqual(self.git("symbolic-ref", "--short", "HEAD"), branch)
        self.assertEqual(self.git("log", "-1", "--format=%s"), "Release qt-applications 1.1 and qt-tools 1.1")
        self.assertEqual(self.git("rev-parse", "HEAD~1"), self.git("rev-parse", "origin/main"))
        self.assertTrue((self.root / "README").exists())
        self.assertEqual(
            self.git("diff", "--name-only", "HEAD~1").splitlines(),
            [release.version_path("qt-applications"), release.version_path("qt-tools")],
        )
        self.assertEqual(release.version_at(self.root, "HEAD", "qt-tools"), "1.1")
        self.assertEqual(release.version_at(self.root, "HEAD", "pyqt-tools"), "1.1.dev0")
        self.assertEqual(
            subprocess.run(["git", "rev-parse", branch], cwd=self.origin, check=True, capture_output=True,
                           text=True).stdout.strip(),
            self.git("rev-parse", "HEAD"),
        )
        [create] = [command for command in self.commands if command[0] == "gh"]
        self.assertEqual(create[create.index("--label") + 1], "enqueue")
        self.assertIn(("git", "commit", "--gpg-sign", "--message", "Release qt-applications 1.1 and qt-tools 1.1"),
                      self.commands)

    def assert_refused(self, pattern, *specs):
        head = self.git("rev-parse", "HEAD")
        with self.assertRaisesRegex(ReleaseError, pattern):
            self.prepare(*specs)
        self.assertEqual(self.git("symbolic-ref", "--short", "HEAD"), "main")
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertFalse(any(command[:2] == ("git", "push") for command in self.commands))

    def test_arguments(self):
        self.assert_refused("Expected <package>=<version>", "qt-tools")
        self.assert_refused("Expected <package>=<version>", "other=1.0")
        self.assert_refused("listed twice", "qt-tools=1.1", "qt-tools=1.2")
        self.assert_refused("must be final", "qt-tools=1.1.dev0")

    def test_downgrade(self):
        self.assert_refused("not newer than the current 1.1.dev0", "qt-tools=1.0")
        self.assert_refused("not newer than the current 1.1.dev0", "qt-tools=1.0.5")

    def test_existing_tag(self):
        self.git("tag", "qt-tools-v1.2", "HEAD~1")
        self.assert_refused("not newer than qt-tools-v1.2", "qt-tools=1.2")

    def test_existing_remote_branch(self):
        subprocess.run(["git", "branch", "release/qt-applications-v1.1", "main"], cwd=self.origin, check=True)
        self.assert_refused("release/qt-applications-v1.1 or a release tag already exists", "qt-applications=1.1")

    def test_release_order(self):
        self.write("packages/qt-tools/setup.py", "# changed\n")
        self.commit("Change qt-tools")
        self.git("push", "--quiet", "origin", "main")
        self.assert_refused("pyqt-tools needs qt-tools", "pyqt-tools=1.1")

    def test_untagged_release_elsewhere(self):
        self.set_version("pyqt-plugins", "1.1")
        self.commit("Set by hand")
        self.git("push", "--quiet", "origin", "main")
        self.assert_refused("pyqt-plugins is already at the untagged release 1.1", "qt-tools=1.1")

    def test_requires_main(self):
        self.git("switch", "--quiet", "--create", "other")
        with self.assertRaisesRegex(ReleaseError, "Check out main"):
            self.prepare("qt-tools=1.1")

    def test_requires_clean_tree(self):
        self.write("untracked", "")
        with self.assertRaisesRegex(ReleaseError, "working tree has changes"):
            self.prepare("qt-tools=1.1")

    def test_requires_origin(self):
        def runner(root, *command):
            if command == ("git", "remote", "get-url", "origin"):
                return "https://github.com/someone/fork"
            return release.run(root, *command)

        with self.assertRaisesRegex(ReleaseError, "origin must be"):
            release.prepare(self.root, ["qt-tools=1.1"], runner=runner)


if __name__ == "__main__":
    unittest.main()
