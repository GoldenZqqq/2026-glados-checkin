import io
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

import checkin

COOKIE = 'gld:sess=fake; gld:sess.sig=fake'


class StatusPushExitCodeTests(unittest.TestCase):
    """只读状态推送的退出码只反映账号查询结果，不受通知渠道故障影响。"""

    def _run(self, status_ok, push_ok, env=None):
        client = checkin.GLaDOS(COOKIE)
        client.req = mock.Mock(return_value={'points': '270', 'history': [], 'plans': {}})
        client.get_status = mock.Mock(return_value=status_ok)
        client.get_points = mock.Mock(return_value=status_ok)
        base_env = {'GLADOS_COOKIE': COOKIE, 'PUSHPLUS_TOKEN': 'fake-token'}
        base_env.update(env or {})
        with mock.patch.dict(os.environ, base_env, clear=True), \
                mock.patch('checkin.GLaDOS', return_value=client), \
                mock.patch('checkin.pushplus', return_value=push_ok):
            return checkin.notify_status_accounts([COOKIE])

    def test_pushplus_unverified_still_exits_zero(self):
        # PushPlus 未实名时接口返回 905：只告警，运行结果仍为成功。
        self.assertEqual(self._run(status_ok=True, push_ok=False), 0)

    def test_push_failure_is_logged_as_warning(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self._run(status_ok=True, push_ok=False)
        self.assertIn('通知渠道发送失败', buffer.getvalue())

    def test_status_query_failure_still_exits_nonzero(self):
        self.assertEqual(self._run(status_ok=False, push_ok=True), 1)


if __name__ == '__main__':
    unittest.main()
