"""pytest configuration and shared fixtures.
pytest 配置和公用 fixture。
"""
import pytest


def pytest_configure(config):
    """Register custom marks / 注册自定义标记。"""
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "visual: mark test as requiring OCP viewer")


@pytest.fixture
def tmp_cache(tmp_path):
    """Temporary cache directory for STEP export tests.
    用于 STEP 导出测试的临时缓存目录。
    """
    cache = tmp_path / "cache"
    cache.mkdir()
    return cache
