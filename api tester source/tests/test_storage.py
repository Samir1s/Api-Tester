import os
import tempfile
import json
from storage import Storage


def test_env_crud():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        s = Storage(db_path=path)
        # create
        env_id = s.create_environment('test', '{"API_URL": "https://example.com"}')
        assert env_id is not None
        envs = s.get_environments()
        assert any(e.name == 'test' for e in envs)
        # update
        assert s.update_environment(env_id, '{"API_URL": "https://api.local"}')
        e = s.get_environment(env_id)
        assert 'api.local' in (e.variables or '')
        # delete
        assert s.delete_environment(env_id)
        assert s.get_environment(env_id) is None
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def test_template_crud():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        s = Storage(db_path=path)
        t_id = s.save_template(name='t1', method='GET', url='https://httpbin.org/get', headers='{}', body='')
        assert t_id is not None
        templates = s.get_templates()
        assert any(t.name == 't1' for t in templates)
        t = s.get_template(t_id)
        assert t is not None and t.method == 'GET'
        assert s.delete_template(t_id)
        assert s.get_template(t_id) is None
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
