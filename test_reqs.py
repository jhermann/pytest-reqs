from pretend import stub
import pytest

pytest_plugins = "pytester",


def test_version():
    import pytest_reqs
    assert pytest_reqs.__version__


@pytest.fixture
def mock_dist():
    return stub(project_name='foo', version='1.0')


@pytest.mark.parametrize('requirements', [
    'foo',
    'foo==1.0',
    'foo>=1.0',
    'foo<=1.0',
])
def test_existing_requirement(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements=requirements)
    monkeypatch.setattr(
        'pytest_reqs.get_installed_distributions',
        lambda: [mock_dist]
    )

    result = testdir.runpytest("--reqs")
    assert 'passed' in result.stdout.str()


def test_missing_requirement(mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements='foo')
    monkeypatch.setattr('pytest_reqs.get_installed_distributions', lambda: [])

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines([
        '*Distribution "foo" is not installed*',
        "*1 failed*",
    ])
    assert 'passed' not in result.stdout.str()


@pytest.mark.parametrize('requirements', [
    'foo==2.0',
    'foo>1.0',
    'foo<1.0',
])
def test_wrong_version(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements=requirements)
    monkeypatch.setattr(
        'pytest_reqs.get_installed_distributions',
        lambda: [mock_dist]
    )

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines([
        '*Distribution "foo" requires %s*' % (requirements),
        "*1 failed*",
    ])
    assert 'passed' not in result.stdout.str()


@pytest.mark.parametrize('requirements', [
    'foo=1.0',
    'foo=>1.0',
])
def test_invalid_requirement(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements='foo=1.0')
    monkeypatch.setattr(
        'pytest_reqs.get_installed_distributions',
        lambda: [mock_dist]
    )

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines([
        '*Invalid requirement*',
        "*1 failed*",
    ])
    assert 'passed' not in result.stdout.str()


def test_missing_local_requirement(testdir, monkeypatch):
    testdir.makefile('.txt', requirements='-e ../foo')
    monkeypatch.setattr('pytest_reqs.get_installed_distributions', lambda: [])

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines([
        '*foo should either be a path to a local project*',
    ])
    assert 'passed' not in result.stdout.str()


def test_local_requirement_ignored(testdir, monkeypatch):
    testdir.makefile('.txt', requirements='-e ../foo')
    testdir.makeini('[pytest]\nreqsignorelocal=True')
    monkeypatch.setattr('pytest_reqs.get_installed_distributions', lambda: [])

    result = testdir.runpytest("--reqs")
    assert 'passed' in result.stdout.str()
