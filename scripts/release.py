#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Prepare, tag, publish and follow up releases of the four packages.

See docs/release.md.  `prepare` runs locally through `mise run release`.  The
other commands run in .github/workflows/ci.yml:

- plan: on a tag push, decide whether this run publishes, and what.
- tag: on main, tag each package whose version is a new release.
- collect: gather and check the wheels a release run publishes.
- github-release: create one GitHub Release per tag with its wheels.
- post-release: open a PR moving released packages to their next .dev0.

Git refs are only created through the GitHub API or pushed by `prepare`.
Nothing here deletes, moves or replaces an existing tag or branch.
"""

import argparse
import base64
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlencode

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY = "altendky/pyqt-tools"
# Dependency order: each package depends on those before it.
PACKAGES = ("qt-applications", "qt-tools", "pyqt-plugins", "pyqt-tools")
# Files outside a package's directory that change its wheels.
EXTRA_SOURCES = {
    "qt-applications": (".github/scripts/platform_tag.py",),
    "pyqt-plugins": (".github/scripts/platform_tag.py",),
}
NUMBER = r"(?:0|[1-9][0-9]*)"
VERSION = re.compile(rf"(?P<release>{NUMBER}(?:\.{NUMBER})*)(?:\.dev(?P<dev>{NUMBER}))?")
VERSION_LINE = re.compile(r'^__version__ = "([^"\n]*)"$', re.MULTILINE)


class ReleaseError(Exception):
    """A release precondition failed.  Existing refs are left unchanged."""


# Versions


def parse_version(value):
    """Return a sort key for a package version such as 2.4 or 2.5.dev0."""
    match = VERSION.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise ReleaseError(f"Invalid version {value!r}; expected X.Y or X.Y.devN without leading zeros")
    release = [int(part) for part in match["release"].split(".")]
    while len(release) > 1 and release[-1] == 0:
        release.pop()
    dev = match["dev"]
    return (tuple(release), dev is None, int(dev or 0))


def is_final(version):
    return parse_version(version)[1]


def final_version(value):
    if not is_final(value):
        raise ReleaseError(f"Release versions must be final, such as 2.4, not {value!r}")
    return value


def next_dev(version):
    """The development version after a release: 2.4 becomes 2.5.dev0."""
    release = [int(part) for part in final_version(version).split(".")]
    release[-1] += 1
    return ".".join(map(str, release)) + ".dev0"


def version_path(package):
    return f"packages/{package}/src/{package.replace('-', '_')}/_version.py"


def read_version_text(text, label):
    found = VERSION_LINE.findall(text)
    if len(found) != 1:
        raise ReleaseError(f"{label}: expected one __version__ line, found {len(found)}")
    parse_version(found[0])
    return found[0]


def replace_version_text(text, version, label):
    read_version_text(text, label)
    parse_version(version)
    return VERSION_LINE.sub(f'__version__ = "{version}"', text)


def tag_name(package, version):
    return f"{package}-v{version}"


def parse_tag(tag):
    """Return (package, version) for a final package release tag, else None."""
    for package in PACKAGES:
        prefix = f"{package}-v"
        if tag.startswith(prefix):
            version = tag[len(prefix):]
            try:
                if is_final(version):
                    return package, version
            except ReleaseError:
                pass
            return None
    return None


@dataclasses.dataclass(frozen=True)
class Release:
    package: str
    version: str

    @property
    def tag(self):
        return tag_name(self.package, self.version)

    def to_json(self):
        return {"package": self.package, "version": self.version, "tag": self.tag}

    @classmethod
    def from_json(cls, item):
        release = cls(item["package"], final_version(item["version"]))
        if release.package not in PACKAGES or item.get("tag") != release.tag:
            raise ReleaseError(f"Invalid release entry: {item!r}")
        return release


def releases_from_environment(environ):
    try:
        items = json.loads(environ.get("RELEASES", ""))
    except json.JSONDecodeError as error:
        raise ReleaseError("RELEASES must be the JSON list from the release plan") from error
    releases = [Release.from_json(item) for item in items]
    if not releases or [r.package for r in releases] != [p for p in PACKAGES if p in {r.package for r in releases}]:
        raise ReleaseError("RELEASES must list distinct packages in dependency order")
    return releases


# Git


def git(root, *args, check=True):
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if check and result.returncode:
        raise ReleaseError(f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result


def git_output(root, *args):
    return git(root, *args).stdout.strip()


def local_tags(root):
    """Map each tag name to the commit it identifies."""
    output = git_output(
        root, "for-each-ref", "--format=%(refname:strip=2) %(objectname) %(*objectname)", "refs/tags",
    )
    tags = {}
    for line in output.splitlines():
        name, sha, *peeled = line.split()
        tags[name] = peeled[0] if peeled else sha
    return tags


def is_ancestor(root, ancestor, descendant):
    result = git(root, "merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if result.returncode not in (0, 1):
        raise ReleaseError(f"Cannot compare {ancestor} with {descendant}: {result.stderr.strip()}")
    return result.returncode == 0


def version_at(root, commit, package):
    path = version_path(package)
    result = git(root, "show", f"{commit}:{path}", check=False)
    if result.returncode:
        raise ReleaseError(f"Cannot read {path} at {commit}")
    return read_version_text(result.stdout, f"{path} at {commit}")


def latest_release_tag(tags, package):
    """The highest final release tag of a package, ignoring other tag forms."""
    found = [(parse_version(parsed[1]), tag) for tag in tags if (parsed := parse_tag(tag)) and parsed[0] == package]
    return max(found)[1] if found else None


def last_release(root, tags, package, head):
    """The highest final release tag of a package in the history of head."""
    found = [
        (parse_version(parsed[1]), tag)
        for tag, sha in tags.items()
        if (parsed := parse_tag(tag)) and parsed[0] == package and is_ancestor(root, sha, head)
    ]
    return max(found)[1] if found else None


def changed_since(root, package, base, head):
    """Whether a package's sources differ between two commits, ignoring its version."""
    paths = [f"packages/{package}", *EXTRA_SOURCES.get(package, ()), f":(exclude){version_path(package)}"]
    result = git(root, "diff", "--quiet", base, head, "--", *paths, check=False)
    if result.returncode not in (0, 1):
        raise ReleaseError(f"Cannot compare {package} between {base} and {head}: {result.stderr.strip()}")
    return result.returncode == 1


def check_release_order(root, tags, head, releasing):
    """Refuse releases tested against unreleased upstream changes (#140).

    Each released package was tested with the upstream wheels built from head.
    Users get the upstream packages from PyPI, so every upstream package must
    either be released too or be unchanged since its last release.
    """
    problems = []
    for index, package in enumerate(PACKAGES):
        if package not in releasing:
            continue
        for upstream in PACKAGES[:index]:
            if upstream in releasing:
                continue
            last = last_release(root, tags, upstream, head)
            if last is None:
                problems.append(f"{package} needs {upstream}, which has no release tag; release {upstream} too")
            elif changed_since(root, upstream, tags[last], head):
                problems.append(f"{package} needs {upstream}, which changed since {last}; release {upstream} too")
    if problems:
        raise ReleaseError("Release order (#140):\n  " + "\n  ".join(problems))


def pending_releases(root, tags, head):
    """Packages whose version at head is a release not tagged at another commit.

    The result is in dependency order and depends only on head and on tags
    outside head, so every tag run at head computes the same result while
    the tags are being created.
    """
    releases = []
    for package in PACKAGES:
        version = version_at(root, head, package)
        if not is_final(version):
            continue
        release = Release(package, version)
        target = tags.get(release.tag)
        if target is not None and target != head:
            print(f"{release.tag} was already released at {target}; not releasing it again")
            continue
        releases.append(release)
    return releases


# GitHub


class GitHub:
    def __init__(self, repository, root=ROOT):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository or ""):
            raise ReleaseError("GITHUB_REPOSITORY must be owner/repository")
        self.repository = repository
        self.root = root

    def gh(self, *args, input_text=None):
        result = subprocess.run(
            ["gh", *args], cwd=self.root, input=input_text, text=True, capture_output=True,
        )
        if result.returncode:
            raise ReleaseError(f"gh {args[0]} {args[1]} failed: {result.stderr.strip() or result.stdout.strip()}")
        return result.stdout

    def api(self, endpoint, *, method="GET", data=None, missing_ok=False):
        args = ["gh", "api", f"repos/{self.repository}/{endpoint}", "--method", method]
        if data is not None:
            args += ["--input", "-"]
        result = subprocess.run(
            args, cwd=self.root, input=None if data is None else json.dumps(data),
            text=True, capture_output=True,
        )
        if result.returncode:
            if missing_ok and "(HTTP 404)" in result.stderr:
                return None
            raise ReleaseError(f"GitHub {method} {endpoint}: {result.stderr.strip()}")
        return json.loads(result.stdout) if result.stdout.strip() else None

    def graphql(self, payload):
        response = json.loads(self.gh("api", "graphql", "--input", "-", input_text=json.dumps(payload)))
        if response.get("errors"):
            raise ReleaseError(f"GitHub GraphQL errors: {json.dumps(response['errors'])}")
        return response["data"]

    def ref(self, name):
        """The commit a ref such as heads/main or tags/x identifies, or None."""
        ref = self.api(f"git/ref/{quote(name, safe='/')}", missing_ok=True)
        if ref is None:
            return None
        obj = ref["object"]
        for _ in range(10):
            if obj["type"] == "commit":
                return obj["sha"]
            if obj["type"] != "tag":
                break
            obj = self.api(f"git/tags/{obj['sha']}")["object"]
        raise ReleaseError(f"{name} does not identify a commit")

    def create_ref(self, name, sha):
        try:
            self.api("git/refs", method="POST", data={"ref": f"refs/{name}", "sha": sha})
        except ReleaseError:
            # Another run may have created this exact ref, or the response was
            # lost.  Never accept or replace a ref at another commit.
            if self.ref(name) != sha:
                raise

    def fast_forward(self, name, sha):
        self.api(f"git/refs/{quote(name, safe='/')}", method="PATCH", data={"sha": sha, "force": False})

    def contains(self, ancestor, descendant):
        status = self.api(f"compare/{ancestor}...{descendant}")["status"]
        return status in {"ahead", "identical"}

    def contents(self, path, ref):
        item = self.api(f"contents/{quote(path, safe='/')}?{urlencode({'ref': ref})}")
        if item.get("type") != "file" or item.get("encoding") != "base64":
            raise ReleaseError(f"Cannot read {path} at {ref}")
        return base64.b64decode(item["content"]).decode("utf-8")


def write_outputs(environ, outputs):
    for key, value in outputs.items():
        print(f"{key}={value}")
    if environ.get("GITHUB_OUTPUT"):
        with open(environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            for key, value in outputs.items():
                output.write(f"{key}={value}\n")


def require_checkout(root, sha):
    if git_output(root, "rev-parse", "HEAD") != sha:
        raise ReleaseError(f"The checkout is not at {sha}")
    if git_output(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ReleaseError("The checkout has changes")


# CI: plan


def plan(root, environ):
    """Decide what this run builds and publishes.

    Every run builds and tests except tag runs that another tag run at the
    same commit publishes for.  The run for the most upstream package being
    released publishes all of them, and tag-release creates its tag last.
    """
    outputs = {"build": "true", "publish": "false", "packages": "[]", "releases": "[]"}
    if environ.get("GITHUB_EVENT_NAME") != "push" or environ.get("GITHUB_REF_TYPE") != "tag":
        return outputs
    tag = environ.get("GITHUB_REF_NAME", "")
    parsed = parse_tag(tag)
    if parsed is None:
        raise ReleaseError(f"{tag!r} is not a release tag such as qt-tools-v1.4")
    sha = environ.get("GITHUB_SHA", "")
    require_checkout(root, sha)
    tags = local_tags(root)
    if tags.get(tag) != sha:
        raise ReleaseError(f"The checkout's {tag} tag does not identify {sha}")
    releases = pending_releases(root, tags, sha)
    if Release(*parsed) not in releases:
        raise ReleaseError(f"{tag} does not match {version_path(parsed[0])} at {sha}")
    check_release_order(root, tags, sha, {r.package for r in releases})
    leader = releases[0]
    if leader.tag != tag:
        print(f"The {leader.tag} run publishes {', '.join(r.tag for r in releases)}")
        return {**outputs, "build": "false"}
    missing = [r.tag for r in releases if tags.get(r.tag) != sha]
    if missing:
        raise ReleaseError(
            f"Tags missing at {sha}: {', '.join(missing)}.  Create them, then rerun this run.",
        )
    print(f"Publishing {', '.join(r.tag for r in releases)}")
    return {
        "build": "true",
        "publish": "true",
        "packages": json.dumps([r.package for r in releases]),
        "releases": json.dumps([r.to_json() for r in releases]),
    }


# CI: tag


def tag_releases(root, github, environ):
    if environ.get("GITHUB_REF") != "refs/heads/main":
        raise ReleaseError("Tagging requires a main run")
    sha = environ.get("GITHUB_SHA", "")
    if github.ref("heads/main") != sha:
        raise ReleaseError("This run is no longer for the current main; refusing to tag a stale commit")
    require_checkout(root, sha)
    tags = local_tags(root)
    releases = pending_releases(root, tags, sha)
    if not releases:
        print("No new release versions")
        return []
    check_release_order(root, tags, sha, {r.package for r in releases})
    remote = {r.tag: github.ref(f"tags/{r.tag}") for r in releases}
    for release in releases:
        if remote[release.tag] not in (None, sha):
            raise ReleaseError(f"{release.tag} already identifies {remote[release.tag]}; leaving it unchanged")
    # The most upstream tag goes last.  Its run publishes them all, so the
    # others must exist when it starts.
    for release in reversed(releases):
        if remote[release.tag] == sha:
            print(f"{release.tag} already identifies {sha}")
            continue
        if github.ref("heads/main") != sha:
            raise ReleaseError("Main advanced while tagging; refusing to tag a stale commit")
        github.create_ref(f"tags/{release.tag}", sha)
        print(f"Created {release.tag} at {sha}")
    return releases


# CI: wheels and GitHub Releases


def wheel_names(package):
    prefix, _, rest = package.partition("-")
    return {f"{prefix}{major}_{rest}" for major in ("5", "6")}


def check_wheel(package, version, path):
    parts = path.name.split("-")
    if len(parts) < 5 or path.suffix != ".whl":
        raise ReleaseError(f"Not a wheel file name: {path.name}")
    name, wheel_version = parts[:2]
    if name not in wheel_names(package):
        raise ReleaseError(f"{path.name} is not a {package} wheel")
    if not re.fullmatch(rf"[0-9]+\.[0-9]+\.[0-9]+\.{re.escape(version)}", wheel_version):
        raise ReleaseError(f"{path.name} does not have version <Qt version>.{version}")
    return name.replace("_", "-"), wheel_version


def collect(releases, artifacts, dist):
    """Copy each package's wheels from artifacts/<package>/ into dist/<package>/."""
    for release in releases:
        found = {}
        for path in sorted((artifacts / release.package).rglob("*.whl")):
            check_wheel(release.package, release.version, path)
            if path.name in found and found[path.name].read_bytes() != path.read_bytes():
                raise ReleaseError(f"Different wheels share the name {path.name}")
            found[path.name] = path
        if not found:
            raise ReleaseError(f"No wheels found for {release.tag}")
        destination = dist / release.package
        destination.mkdir(parents=True, exist_ok=False)
        for name, path in sorted(found.items()):
            shutil.copyfile(path, destination / name)
            print(f"{release.tag}: {name}")


def release_notes(release, wheels):
    published = sorted({check_wheel(release.package, release.version, wheel) for wheel in wheels})
    lines = [f"{release.package} {release.version}, published to PyPI as:", ""]
    lines += [f"- [{name} {version}](https://pypi.org/project/{name}/{version}/)" for name, version in published]
    return "\n".join(lines) + "\n"


def sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def find_release(github, tag):
    release = github.api(f"releases/tags/{quote(tag, safe='')}", missing_ok=True)
    if release is not None:
        return release
    # Drafts are only found by listing.  A recent one is on the first page.
    for item in github.api("releases?per_page=100"):
        if item.get("tag_name") == tag:
            return item
    return None


def github_releases(github, releases, dist):
    for release in releases:
        wheels = sorted((dist / release.package).glob("*.whl"))
        if not wheels:
            raise ReleaseError(f"No wheels to attach to {release.tag}")
        existing = find_release(github, release.tag)
        if existing is None:
            with tempfile.TemporaryDirectory() as directory:
                notes = pathlib.Path(directory) / "notes.md"
                notes.write_text(release_notes(release, wheels), encoding="utf-8")
                github.gh(
                    "release", "create", release.tag, "--repo", github.repository, "--verify-tag",
                    "--title", release.tag, "--notes-file", str(notes), *map(str, wheels),
                )
            print(f"Created the {release.tag} release")
            continue
        assets = {asset["name"]: asset for asset in existing.get("assets", [])}
        missing = []
        for wheel in wheels:
            asset = assets.get(wheel.name)
            if asset is None:
                missing.append(wheel)
            elif asset.get("digest") not in (None, sha256(wheel)) or asset.get("size") != wheel.stat().st_size:
                raise ReleaseError(f"The {release.tag} release has a different {wheel.name}; leaving it unchanged")
        if missing:
            github.gh("release", "upload", release.tag, "--repo", github.repository, *map(str, missing))
        if existing.get("draft"):
            github.gh("release", "edit", release.tag, "--repo", github.repository, "--draft=false")
        print(f"The {release.tag} release is complete")


# CI: post-release


def pr_templates(root):
    paths = [root / name for name in (
        "pull_request_template.md", ".github/pull_request_template.md", "docs/pull_request_template.md",
    )]
    template_directory = root / ".github/PULL_REQUEST_TEMPLATE"
    if template_directory.is_dir():
        paths.extend(template_directory.iterdir())
    return [path for path in paths if path.is_file()]


def describe(versions):
    items = [f"{package} {version}" for package, version in versions.items()]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def post_release(root, github, releases):
    if pr_templates(root):
        raise ReleaseError("A PR template exists; update post-release to fill it in")
    main = github.ref("heads/main")
    bumps = {}
    changes = {}
    for release in releases:
        path = version_path(release.package)
        text = github.contents(path, main)
        current = read_version_text(text, f"{path} on main")
        if current == release.version:
            bumps[release.package] = next_dev(release.version)
            changes[path] = replace_version_text(text, bumps[release.package], path)
        else:
            print(f"{release.package} is already at {current} on main")
    if not bumps:
        print("No post-release version changes needed")
        return None
    message = f"Start {describe(bumps)} development"
    branch = "post-release/" + "+".join(r.tag for r in releases)
    head = github.ref(f"heads/{branch}")
    if head is None:
        github.create_ref(f"heads/{branch}", main)
        head = main
    if head != main and github.contains(head, main):
        # An earlier attempt created the branch and stopped before committing.
        github.fast_forward(f"heads/{branch}", main)
        head = main
    if head == main:
        head = create_commit(github, branch, main, message, changes)
    verify_commit(github, head, main, message, changes)
    return ensure_pull_request(github, branch, head, message, releases)


def create_commit(github, branch, base, message, changes):
    """Commit through the API so that GitHub signs the commit."""
    data = github.graphql({
        "query": (
            "mutation($input: CreateCommitOnBranchInput!) "
            "{ createCommitOnBranch(input: $input) { commit { oid } } }"
        ),
        "variables": {"input": {
            "branch": {"repositoryNameWithOwner": github.repository, "branchName": branch},
            "expectedHeadOid": base,
            "message": {"headline": message},
            "fileChanges": {"additions": [
                {"path": path, "contents": base64.b64encode(text.encode("utf-8")).decode("ascii")}
                for path, text in sorted(changes.items())
            ]},
        }},
    })
    return data["createCommitOnBranch"]["commit"]["oid"]


def verify_commit(github, sha, main, message, changes):
    commit = github.api(f"git/commits/{sha}")
    parents = [parent["sha"] for parent in commit.get("parents", [])]
    if (
        commit.get("message") != message
        or len(parents) != 1
        or not commit.get("verification", {}).get("verified")
        or not github.contains(parents[0], main)
    ):
        raise ReleaseError(f"The post-release branch at {sha} is not the expected signed commit; leaving it unchanged")
    files = github.api(f"compare/{parents[0]}...{sha}").get("files", [])
    if {item["filename"] for item in files} != changes.keys() or any(
        github.contents(path, sha) != text for path, text in changes.items()
    ):
        raise ReleaseError(f"The post-release branch at {sha} has unexpected changes; leaving it unchanged")


def ensure_pull_request(github, branch, sha, message, releases):
    owner = github.repository.split("/")[0]
    query = urlencode({"state": "all", "head": f"{owner}:{branch}", "base": "main", "per_page": 100})
    pulls = github.api(f"pulls?{query}")
    for pull in pulls:
        if pull["state"] == "open":
            if pull["head"]["sha"] != sha:
                raise ReleaseError(f"{pull['html_url']} has other commits; leaving it unchanged")
            if not any(label["name"] == "enqueue" for label in pull.get("labels", [])):
                github.api(f"issues/{pull['number']}/labels", method="POST", data={"labels": ["enqueue"]})
            return pull["html_url"]
    if pulls:
        raise ReleaseError(f"The post-release PR was closed; leaving it unchanged: {pulls[0]['html_url']}")
    body = (
        f"{message} after releasing {', '.join(r.tag for r in releases)}.\n\n"
        "Opened by the release workflow; see docs/release.md.\n"
    )
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "body.md"
        path.write_text(body, encoding="utf-8")
        return github.gh(
            "pr", "create", "--repo", github.repository, "--base", "main", "--head", branch,
            "--title", f"Post-release: {message[0].lower()}{message[1:]}",
            "--body-file", str(path), "--label", "enqueue",
        ).strip()


# Local: prepare


def run(root, *command):
    result = subprocess.run(
        command, cwd=root, text=True, stdout=subprocess.PIPE,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode:
        raise ReleaseError(f"{' '.join(command)} failed; stopped without retrying")
    return result.stdout.strip()


def parse_requests(specs):
    requests = {}
    for spec in specs:
        package, separator, version = spec.partition("=")
        if not separator or package not in PACKAGES:
            raise ReleaseError(f"Expected <package>=<version> with a package from {', '.join(PACKAGES)}: {spec!r}")
        if package in requests:
            raise ReleaseError(f"{package} is listed twice")
        requests[package] = final_version(version)
    if not requests:
        raise ReleaseError("Name at least one <package>=<version>")
    return {package: requests[package] for package in PACKAGES if package in requests}


def prepare(root, specs, *, body_file=None, runner=run):
    """Open a signed release PR for the requested package versions."""
    requests = parse_requests(specs)
    if pathlib.Path(runner(root, "git", "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise ReleaseError("Run this from the pyqt-tools repository")
    if runner(root, "git", "symbolic-ref", "--short", "HEAD") != "main":
        raise ReleaseError("Check out main first")
    if runner(root, "git", "status", "--porcelain=v1", "--untracked-files=all"):
        raise ReleaseError("The working tree has changes")
    origin = runner(root, "git", "remote", "get-url", "origin").removesuffix(".git")
    if origin not in (
        f"git@github.com:{REPOSITORY}", f"https://github.com/{REPOSITORY}", f"ssh://git@github.com/{REPOSITORY}",
    ):
        raise ReleaseError(f"origin must be {REPOSITORY}")
    if body_file is not None:
        body_file = pathlib.Path(body_file).resolve(strict=True)
        if not body_file.read_text(encoding="utf-8").strip():
            raise ReleaseError("The PR body file is empty")
    # Remote operations run one at a time and are never retried.
    runner(root, "git", "fetch", "--tags", "origin")
    runner(root, "git", "merge", "--ff-only", "origin/main")
    head = runner(root, "git", "rev-parse", "HEAD")
    if head != runner(root, "git", "rev-parse", "origin/main"):
        raise ReleaseError("main has commits that origin/main does not; stopping")
    if body_file is None and pr_templates(root):
        raise ReleaseError("A PR template exists; pass --body-file with it filled in")
    tags = local_tags(root)
    for package in PACKAGES:
        current = version_at(root, head, package)
        if package in requests:
            version = requests[package]
            latest = latest_release_tag(tags, package)
            if parse_version(version) <= parse_version(current):
                raise ReleaseError(f"{package}: {version} is not newer than the current {current}")
            if latest is not None and parse_version(version) <= parse_version(parse_tag(latest)[1]):
                raise ReleaseError(f"{package}: {version} is not newer than {latest}")
        elif is_final(current) and tag_name(package, current) not in tags:
            raise ReleaseError(f"{package} is already at the untagged release {current}; include or fix it")
    releases = [Release(package, version) for package, version in requests.items()]
    branch = "release/" + "+".join(r.tag for r in releases)
    refs = [f"refs/heads/{branch}", f"refs/remotes/origin/{branch}", *(f"refs/tags/{r.tag}" for r in releases)]
    if runner(root, "git", "for-each-ref", "--format=%(refname)", *refs):
        raise ReleaseError(f"{branch} or a release tag already exists locally")
    remote_refs = [f"refs/heads/{branch}", *(f"refs/tags/{r.tag}" for r in releases)]
    if runner(root, "git", "ls-remote", "origin", *remote_refs):
        raise ReleaseError(f"{branch} or a release tag already exists on origin")
    check_release_order(root, tags, head, set(requests))
    title = f"Release {describe(requests)}"
    runner(root, "git", "switch", "--create", branch)
    paths = []
    for release in releases:
        path = version_path(release.package)
        file = root / path
        file.write_text(replace_version_text(file.read_text(encoding="utf-8"), release.version, path), encoding="utf-8")
        paths.append(path)
    runner(root, "git", "add", "--", *paths)
    runner(root, "git", "commit", "--gpg-sign", "--message", title)
    runner(root, "git", "push", "--set-upstream", "origin", branch)
    if body_file is None:
        with tempfile.TemporaryDirectory() as directory:
            body_file = pathlib.Path(directory) / "body.md"
            body_file.write_text(
                f"{title}.\n\n"
                f"After this merges and main's `all` check passes, CI tags {', '.join(r.tag for r in releases)} "
                "and the tag run publishes them once the `pypi` environment is approved.  "
                "See docs/release.md.\n",
                encoding="utf-8",
            )
            return create_pull_request(root, runner, branch, title, body_file)
    return create_pull_request(root, runner, branch, title, body_file)


def create_pull_request(root, runner, branch, title, body_file):
    return runner(
        root, "gh", "pr", "create", "--repo", REPOSITORY, "--base", "main", "--head", branch,
        "--title", title, "--body-file", str(body_file), "--label", "enqueue",
    )


# Command line


def main(argv=None, environ=os.environ):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare", help="open a release PR")
    preparation.add_argument("versions", nargs="+", metavar="PACKAGE=VERSION")
    preparation.add_argument("--body-file", type=pathlib.Path)
    commands.add_parser("plan")
    commands.add_parser("tag")
    collection = commands.add_parser("collect")
    collection.add_argument("artifacts", type=pathlib.Path)
    collection.add_argument("dist", type=pathlib.Path)
    publication = commands.add_parser("github-release")
    publication.add_argument("dist", type=pathlib.Path)
    commands.add_parser("post-release")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            print(prepare(ROOT, args.versions, body_file=args.body_file))
        elif args.command == "plan":
            write_outputs(environ, plan(ROOT, environ))
        elif args.command == "tag":
            tag_releases(ROOT, GitHub(environ.get("GITHUB_REPOSITORY"), ROOT), environ)
        elif args.command == "collect":
            collect(releases_from_environment(environ), args.artifacts, args.dist)
        elif args.command == "github-release":
            github_releases(GitHub(environ.get("GITHUB_REPOSITORY"), ROOT), releases_from_environment(environ), args.dist)
        elif args.command == "post-release":
            url = post_release(ROOT, GitHub(environ.get("GITHUB_REPOSITORY"), ROOT), releases_from_environment(environ))
            if url:
                print(url)
    except ReleaseError as error:
        parser.exit(1, f"release: {error}\n")


if __name__ == "__main__":
    main()
