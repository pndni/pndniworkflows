import pytest
import os


@pytest.fixture()
def cdtmppath(tmp_path):
    curdir = os.getcwd()
    os.chdir(str(tmp_path))
    yield tmp_path
    os.chdir(curdir)
