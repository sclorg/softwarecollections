import os
from pathlib import Path
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory

from tito.builder import Builder
from tito.common import run_command, debug, find_spec_file


class TemporaryWorktree(TemporaryDirectory):
    """Create temporary git checkout to different directory"""

    def __init__(self, *args, commit="HEAD", **kwargs):
        """Store identification of desired commit"""

        super().__init__(*args, **kwargs)

        self.commit = commit
        self.orig_dir = None

        create = "git worktree add --detach {path} {commit}".format(
            path=self.name, commit=self.commit
        )
        run_command(create)

    def cleanup(self):
        """Remove refence to the worktree"""

        ret = super().cleanup()
        run_command("git worktree prune")

        return ret

    def __enter__(self):
        """Switch working dir to the worktree.

        Returns: Path to the worktree.
        """

        path = super().__enter__()

        self.orig_dir = Path.cwd()
        os.chdir(path)

        return Path(path)

    def __exit__(self, *exc_info):
        """Switch working dir to the original one"""

        os.chdir(self.orig_dir)
        self.orig_dir = None

        return super().__exit__(*exc_info)


class SetupBuilder(Builder):
    """Build tgz using setup.py sdist"""

    def _setup_sources(self):
        """Create .tar.gz for this package.

        Returns: absolute path to the archive.
        """

        def strip_ext(name, ext=".tar.gz"):
            return name[: -len(ext)]

        self._create_build_dirs()

        target_archive = Path(self.rpmbuild_sourcedir, self.tgz_filename)
        target_root = strip_ext(target_archive.name)

        worktree = TemporaryWorktree(prefix="scl.org.build-", commit=self.git_commit_id)

        with worktree as workdir:
            debug("Copy source directory to {}".format(self.rpmbuild_gitcopy))
            rmtree(self.rpmbuild_gitcopy)
            copytree(workdir, self.rpmbuild_gitcopy)

            debug("Make sdist archive")
            run_command("python3 ./setup.py sdist")

            source_archive, = workdir.joinpath("dist").glob("*.tar.gz")
            source_root = strip_ext(source_archive.name)

            debug("Recreate sdist archive in {target}".format(target=target_archive))
            recreate = [
                "tar -xzf {archive}".format(archive=source_archive),
                "mv {source} {target}".format(source=source_root, target=target_root),
                "tar -czf {archive} {root}".format(
                    archive=target_archive, root=target_root
                ),
            ]
            for command in recreate:
                run_command(command)

        self.spec_file_name = find_spec_file(self.rpmbuild_gitcopy)
        self.spec_file = Path(self.rpmbuild_gitcopy, self.spec_file_name)
