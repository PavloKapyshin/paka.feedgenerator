import pickle
import datetime
import unittest

import pytz

from paka.feedgenerator.utils import timezone


class TimezoneTests(unittest.TestCase):

    def test_fixedoffset_timedelta(self):
        delta = datetime.timedelta(hours=1)
        self.assertEqual(timezone.get_fixed_timezone(delta).utcoffset(''), delta)

    def test_fixedoffset_pickle(self):
        self.assertEqual(pickle.loads(pickle.dumps(timezone.FixedOffset(0, 'tzname'))).tzname(''), 'tzname')
