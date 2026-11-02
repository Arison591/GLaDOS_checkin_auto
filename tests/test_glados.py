import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import requests
import glados


class CheckinTests(unittest.TestCase):
    def response(self, payload):
        result = Mock()
        result.json.return_value = payload
        return result

    def run_account(self, result, status):
        with patch.object(glados.requests, 'post', return_value=self.response(result)) as post:
            with patch.object(glados.requests, 'get', return_value=self.response(status)):
                outcome = glados.checkin('sensitive-test-cookie', 1)
                self.assertEqual(post.call_args.kwargs['timeout'], 30)
                return outcome

    def test_success(self):
        ok, text = self.run_account(
            {'code': 0, 'message': 'Checkin!'},
            {'code': 0, 'data': {'leftDays': '12.34'}},
        )
        self.assertTrue(ok)
        self.assertIn('12', text)
        self.assertNotIn('sensitive-test-cookie', text)

    def test_repeat_checkin(self):
        ok, _ = self.run_account(
            {'code': 1, 'message': 'You have already checked in today.'},
            {'code': 0, 'data': {'leftDays': '12'}},
        )
        self.assertTrue(ok)

    def test_expired_cookie(self):
        ok, _ = self.run_account(
            {'code': 1, 'message': 'Please login'}, {'code': 1},
        )
        self.assertFalse(ok)

    def test_rejected_checkin_with_valid_status(self):
        ok, _ = self.run_account(
            {'code': 1, 'message': 'Please login'},
            {'code': 0, 'data': {'leftDays': '12'}},
        )
        self.assertFalse(ok)

    def test_unexpected_response(self):
        ok, _ = self.run_account([], {'code': 0})
        self.assertFalse(ok)

    def test_timeout_does_not_leak_cookie(self):
        with patch.object(glados.requests, 'post', side_effect=requests.Timeout('sensitive-test-cookie')):
            ok, text = glados.checkin('sensitive-test-cookie', 1)
        self.assertFalse(ok)
        self.assertNotIn('sensitive-test-cookie', text)

    def test_non_json_response(self):
        response = self.response(None)
        response.json.side_effect = ValueError('not json')
        with patch.object(glados.requests, 'post', return_value=response):
            self.assertFalse(glados.checkin('secret', 1)[0])

    def test_missing_cookie(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(glados.requests, 'post') as post:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(glados.main(), 1)
            post.assert_not_called()

    def test_multiple_accounts_continue_after_failure(self):
        with patch.dict(os.environ, {'GLADOS_COOKIE': 'first & & second', 'PUSHPLUS_TOKEN': ''}):
            with patch.object(glados, 'checkin', side_effect=[(False, 'failed'), (True, 'ok')]) as checkin:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(glados.main(), 1)
                self.assertEqual(checkin.call_count, 2)
                self.assertEqual(checkin.call_args.args, ('second', 2))


if __name__ == '__main__':
    unittest.main()
