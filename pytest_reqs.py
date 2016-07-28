from glob import glob
from itertools import chain

from pip import get_installed_distributions
from pip.download import PipSession
from pip.exceptions import InstallationError
from pip.req import parse_requirements
import pytest


__version__ = '0.0.1'


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption(
        '--reqs', action='store_true',
        help="check requirements files against what is installed"
    )


def pytest_collection_modifyitems(config, session, items):
    patterns = [
        'req*.txt', 'req*.pip', 'requirements/*.txt', 'requirements/*.pip'
    ]
    filenames = set(chain.from_iterable(map(glob, patterns)))

    installed_distributions = dict(
        (d.project_name.lower(), d)
        for d in get_installed_distributions()
    )

    items.extend(
        ReqsItem(filename, installed_distributions, config, session)
        for filename in filenames
    )


class ReqsError(Exception):
    """ indicates an error during requirements checks. """


class ReqsItem(pytest.Item, pytest.File):

    def __init__(self, filename, installed_distributions, config, session):
        super(ReqsItem, self).__init__(
            filename, config=config, session=session
        )
        self.add_marker("reqs")
        self.filename = filename
        self.installed_distributions = installed_distributions

    def runtest(self):
        reqs = parse_requirements(self.filename, session=PipSession())

        try:
            name_to_req = dict(
                (r.name, r)
                for r in reqs
                if r.name and self.filename in r.comes_from
            )
        except InstallationError as e:
            raise ReqsError("%s (from -r %s)" % (
                e.args[0].split('\n')[0],
                self.filename,
            ))

        for name, req in name_to_req.items():
            try:
                installed_distribution = self.installed_distributions[name]
            except KeyError:
                raise ReqsError(
                    'Distribution "%s" is not installed' % (name)
                )
            if not req.specifier.contains(installed_distribution.version):
                raise ReqsError(
                    'Distribution "%s" requires %s but %s is installed' % (
                        installed_distribution.project_name,
                        req,
                        installed_distribution.version,
                    ))

    def repr_failure(self, excinfo):
        if excinfo.errisinstance(ReqsError):
            return excinfo.value.args[0]
        return super(ReqsItem, self).repr_failure(excinfo)

    def reportinfo(self):
        return (self.fspath, -1, "requirements-check")
