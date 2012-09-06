import sys
import os
from pip.req import InstallRequirement, _make_build_dir, parse_requirements
from pip.commands.install import InstallCommand
import pkg_resources
from pip.log import logger

unpatched_requirementset_prepare_files = sys.modules['pip.req'].RequirementSet.prepare_files
opts = None

def patched_requirementset_prepare_files(self, finder, force_root_egg_info=False, bundle=False):
    """Prepare process. Create temp directories, download and/or unpack files."""
    unnamed = list(self.unnamed_requirements)
    reqs = list(self.requirements.values())
    while reqs or unnamed:
        if unnamed:
            req_to_install = unnamed.pop(0)
        else:
            req_to_install = reqs.pop(0)
        install = True
        best_installed = False
        if not self.ignore_installed and not req_to_install.editable:
            req_to_install.check_if_exists()
            if req_to_install.satisfied_by:
                if self.upgrade:
                    if not self.force_reinstall:
                        try:
                            url = finder.find_requirement(
                                req_to_install, self.upgrade)
                        except BestVersionAlreadyInstalled:
                            best_installed = True
                            install = False
                        else:
                            # Avoid the need to call find_requirement again
                            req_to_install.url = url.url

                    if not best_installed:
                        req_to_install.conflicts_with = req_to_install.satisfied_by
                        req_to_install.satisfied_by = None
                else:
                    install = False
            if req_to_install.satisfied_by:
                if best_installed:
                    logger.notify('Requirement already up-to-date: %s'
                    % req_to_install)
                else:
                    logger.notify('Requirement already satisfied '
                                  '(use --upgrade to upgrade): %s'
                    % req_to_install)
        if req_to_install.editable:
            logger.notify('Obtaining %s' % req_to_install)
        elif install:
            if req_to_install.url and req_to_install.url.lower().startswith('file:'):
                logger.notify('Unpacking %s' % display_path(url_to_path(req_to_install.url)))
            else:
                logger.notify('Downloading/unpacking %s' % req_to_install)
        logger.indent += 2
        try:
            is_bundle = False
            if req_to_install.editable:
                if req_to_install.source_dir is None:
                    location = req_to_install.build_location(self.src_dir)
                    req_to_install.source_dir = location
                else:
                    location = req_to_install.source_dir
                if not os.path.exists(self.build_dir):
                    _make_build_dir(self.build_dir)
                req_to_install.update_editable(not self.is_download)
                if self.is_download:
                    req_to_install.run_egg_info()
                    req_to_install.archive(self.download_dir)
                else:
                    req_to_install.run_egg_info()
            elif install:
                ##@@ if filesystem packages are not marked
                ##editable in a req, a non deterministic error
                ##occurs when the script attempts to unpack the
                ##build directory

                location = req_to_install.build_location(self.build_dir, not self.is_download)
                ## FIXME: is the existance of the checkout good enough to use it?  I don't think so.
                unpack = True
                url = None
                if not os.path.exists(os.path.join(location, 'setup.py')):
                    ## FIXME: this won't upgrade when there's an existing package unpacked in `location`
                    if req_to_install.url is None:
                        url = finder.find_requirement(req_to_install, upgrade=self.upgrade)
                    else:
                        ## FIXME: should req_to_install.url already be a link?
                        url = Link(req_to_install.url)
                        assert url
                    if url:
                        try:
                            self.unpack_url(url, location, self.is_download)
                        except HTTPError:
                            e = sys.exc_info()[1]
                            logger.fatal('Could not install requirement %s because of error %s'
                            % (req_to_install, e))
                            raise InstallationError(
                                'Could not install requirement %s because of HTTP error %s for URL %s'
                                % (req_to_install, e, url))
                    else:
                        unpack = False
                if unpack:
                    is_bundle = req_to_install.is_bundle
                    if is_bundle:
                        req_to_install.move_bundle_files(self.build_dir, self.src_dir)
                        for subreq in req_to_install.bundle_requirements():
                            reqs.append(subreq)
                            self.add_requirement(subreq)
                    elif self.is_download:
                        req_to_install.source_dir = location
                        req_to_install.run_egg_info()
                        if url and url.scheme in vcs.all_schemes:
                            req_to_install.archive(self.download_dir)
                    else:
                        req_to_install.source_dir = location
                        req_to_install.run_egg_info()
                        if force_root_egg_info:
                            # We need to run this to make sure that the .egg-info/
                            # directory is created for packing in the bundle
                            req_to_install.run_egg_info(force_root_egg_info=True)
                        req_to_install.assert_source_matches_version()
                        #@@ sketchy way of identifying packages not grabbed from an index
                        if bundle and req_to_install.url:
                            self.copy_to_build_dir(req_to_install)
                            install = False
                        # req_to_install.req is only avail after unpack for URL pkgs
                    # repeat check_if_exists to uninstall-on-upgrade (#14)
                    req_to_install.check_if_exists()
                    if req_to_install.satisfied_by:
                        if self.upgrade or self.ignore_installed:
                            req_to_install.conflicts_with = req_to_install.satisfied_by
                            req_to_install.satisfied_by = None
                        else:
                            install = False
            if not is_bundle:
                ## FIXME: shouldn't be globally added:
                finder.add_dependency_links(req_to_install.dependency_links)
                if (req_to_install.extras):
                    logger.notify("Installing extra requirements: %r" % ','.join(req_to_install.extras))
                if not self.ignore_dependencies:
                    for req in req_to_install.requirements(req_to_install.extras):
                        try:
                            name = pkg_resources.Requirement.parse(req).project_name
                        except ValueError:
                            e = sys.exc_info()[1]
                            ## FIXME: proper warning
                            logger.error('Invalid requirement: %r (%s) in requirement %s' % (req, e, req_to_install))
                            continue
                        if self.has_requirement(name):
                            ## FIXME: check for conflict
                            continue
                        subreq = InstallRequirement(req, req_to_install)
                        reqs.append(subreq)
                        self.add_requirement(subreq)
                    # ---- START OF PATCH ----
                    # include requirements.txt if available
                    if req_to_install.editable and req_to_install.source_dir:
                        for subreq in install_requirements_txt(req_to_install.name, req_to_install.source_dir):
                            reqs.append(subreq)
                            self.add_requirement(subreq)
                    # ---- END OF PATCH ----
                if req_to_install.name not in self.requirements:
                    self.requirements[req_to_install.name] = req_to_install
                if self.is_download:
                    self.reqs_to_cleanup.append(req_to_install)
            else:
                self.reqs_to_cleanup.append(req_to_install)

            if install:
                self.successfully_downloaded.append(req_to_install)
                if bundle and (req_to_install.url and req_to_install.url.startswith('file:///')):
                    self.copy_to_build_dir(req_to_install)
        finally:
            logger.indent -= 2

def install_requirements_txt(parent_req_name, source_dir):
    fullpath = os.path.join(source_dir, "requirements.txt")
    logger.notify("Found requirements.txt in {0}, installing extra dependencies.".format(parent_req_name))
    if os.path.exists(fullpath):
        return parse_requirements(fullpath, parent_req_name, None, opts)
    return []

class RInstallCommand(InstallCommand):
    name = 'rinstall'
    usage = '%prog [OPTIONS] PACKAGE_NAMES...'
    summary = 'Recursively install packages'
    bundle = False

    def __init__(self):
        super(RInstallCommand, self).__init__()

    def prerun(self):
        sys.modules['pip.req'].RequirementSet.prepare_files = patched_requirementset_prepare_files

    def postrun(self):
        sys.modules['pip.req'].RequirementSet.prepare_files = unpatched_requirementset_prepare_files

    def run(self, options, args):
        global opts
        opts = options
        retval = None
        try:
            self.prerun()
            retval = super(RInstallCommand, self).run(options, args)
        except:
            self.postrun()
            raise
        self.postrun()
        return retval

RInstallCommand()
