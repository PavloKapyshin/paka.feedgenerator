from __future__ import unicode_literals

import re
import datetime
import unittest
import xml.etree.ElementTree as ET

from paka import feedgenerator
from paka.feedgenerator.utils.timezone import get_fixed_timezone, utc


DEFAULT_TIME = datetime.time(
    hour=0, minute=0, second=0, microsecond=0, tzinfo=utc)


def set_default_time(date):
    return datetime.datetime.combine(date, DEFAULT_TIME)


class FeedgeneratorTest(unittest.TestCase):
    maxDiff = None

    def assert_xml_equal(self, this, other):
        def prepare(unparsed_xml):
            return re.sub(r">[\n ]*<", ">\n<", unparsed_xml.strip())
        self.assertEqual(prepare(this), prepare(other))

    def test_get_tag_uri(self):
        self.assertEqual(
            feedgenerator.get_tag_uri('http://example.org/foo/bar#headline', datetime.date(2004, 10, 25)),
            'tag:example.org,2004-10-25:/foo/bar/headline')

    def test_get_tag_uri_with_port(self):
        self.assertEqual(
            feedgenerator.get_tag_uri(
                'http://www.example.org:8000/2008/11/14/some#headline',
                datetime.datetime(2008, 11, 14, 13, 37, 0)),
            'tag:www.example.org,2008-11-14:/2008/11/14/some/headline')

    def test_rfc2822_date(self):
        self.assertEqual(
            feedgenerator.rfc2822_date(datetime.datetime(2008, 11, 14, 13, 37, 0)),
            "Fri, 14 Nov 2008 13:37:00 -0000")

    def test_rfc2822_date_with_timezone(self):
        self.assertEqual(
            feedgenerator.rfc2822_date(
                datetime.datetime(2008, 11, 14, 13, 37, 0, tzinfo=get_fixed_timezone(60))),
            "Fri, 14 Nov 2008 13:37:00 +0100")

    def test_rfc2822_date_without_time(self):
        self.assertEqual(
            feedgenerator.rfc2822_date(datetime.date(2008, 11, 14)),
            "Fri, 14 Nov 2008 00:00:00 -0000"
        )

    def test_rfc3339_date(self):
        self.assertEqual(
            feedgenerator.rfc3339_date(datetime.datetime(2008, 11, 14, 13, 37, 0)),
            "2008-11-14T13:37:00Z"
        )

    def test_rfc3339_date_with_timezone(self):
        self.assertEqual(
            feedgenerator.rfc3339_date(datetime.datetime(2008, 11, 14, 13, 37, 0, tzinfo=get_fixed_timezone(120))),
            "2008-11-14T13:37:00+02:00"
        )

    def test_rfc3339_date_without_time(self):
        self.assertEqual(
            feedgenerator.rfc3339_date(datetime.date(2008, 11, 14)),
            "2008-11-14T00:00:00Z")

    def test_atom1_mime_type(self):
        atom_feed = feedgenerator.Atom1Feed("title", "link", "description")
        self.assertEqual(
            atom_feed.content_type, "application/atom+xml; charset=utf-8")

    def test_rss_mime_type(self):
        rss_feed = feedgenerator.Rss201rev2Feed("title", "link", "description")
        self.assertEqual(
            rss_feed.content_type, "application/rss+xml; charset=utf-8")

    def test_feed_without_feed_url_gets_rendered_without_atom_link(self):
        feed = feedgenerator.Rss201rev2Feed('title', '/link/', 'descr')
        self.assertIsNone(feed.feed['feed_url'])
        feed_content = feed.writeString('utf-8')
        self.assertNotIn('<atom:link', feed_content)
        self.assertNotIn('href="/feed/"', feed_content)
        self.assertNotIn('rel="self"', feed_content)

    def test_feed_with_feed_url_gets_rendered_with_atom_link(self):
        feed = feedgenerator.Rss201rev2Feed('title', '/link/', 'descr', feed_url='/feed/')
        self.assertEqual(feed.feed['feed_url'], '/feed/')
        feed_content = feed.writeString('utf-8')
        self.assertIn('<atom:link', feed_content)
        self.assertIn('href="/feed/"', feed_content)
        self.assertIn('rel="self"', feed_content)

    def test_latest_post_date_returns_utc_time(self):
        rss_feed = feedgenerator.Rss201rev2Feed('title', 'link', 'description')
        self.assertEqual(rss_feed.latest_post_date().tzinfo, utc)

    def test_atom1_full(self):
        expected = """<?xml version="1.0" encoding="utf-8"?>
        <feed xml:lang="en" xmlns="http://www.w3.org/2005/Atom">
          <title>My mega website</title>
          <link href="https://example.org/" rel="alternate"></link>
          <link href="https://example.org/notes/feed/" rel="self"></link>
          <id>https://example.org/</id>
          <updated>2017-05-03T00:00:00+00:00</updated>
          <author>
            <name>John Doe</name>
            <email>john.doe@example.org</email>
            <uri>https://example.org/~johndoe</uri>
          </author>
          <subtitle>Super Subtitle.</subtitle>
          <category term="site"></category>
          <category term="greeting"></category>
          <category term="maintenance"></category>
          <entry>
            <title>Hello, World!</title>
            <link href="https://example.org/notes/hello/" rel="alternate"></link>
            <updated>2017-01-01T00:00:00+00:00</updated>
            <id>https://example.org/notes/hello/</id>
            <summary type="html">As promised, &lt;code&gt;print('hello, world!')&lt;/code&gt;</summary>
            <category term="greeting"></category>
            <category term="site"></category>
          </entry>
          <entry>
            <title>Some update</title>
            <link href="https://example.org/notes/hello/" rel="alternate"></link>
            <published>2017-03-18T00:00:00+00:00</published>
            <updated>2017-05-03T00:00:00+00:00</updated>
            <id>https://example.org/notes/some-update/</id>
            <summary type="html">I updated something on site.</summary>
            <category term="site"></category>
          </entry>
        </feed>"""

        notes_data = (
            {
                "title": "Hello, World!",
                "link": "https://example.org/notes/hello/",
                "description": (
                    "As promised, <code>print('hello, world!')</code>"),
                "unique_id": "https://example.org/notes/hello/",
                "unique_id_is_permalink": True,
                "updateddate": datetime.date(2017, 1, 1),
                "categories": ("greeting", "site")},
            {
                "title": "Some update",
                "link": "https://example.org/notes/hello/",
                "description": "I updated something on site.",
                "unique_id": "https://example.org/notes/some-update/",
                "unique_id_is_permalink": True,
                "pubdate": datetime.date(2017, 3, 18),
                "updateddate": datetime.date(2017, 5, 3),
                "categories": ("site", )})
        feed = feedgenerator.Atom1Feed(
            title="My mega website",
            subtitle="Super Subtitle.",
            link="https://example.org/",
            language="en",
            author_name="John Doe",
            author_email="john.doe@example.org",
            author_link="https://example.org/~johndoe",
            description=None,
            feed_url="https://example.org/notes/feed/",
            ttl=3134,
            categories=("site", "greeting", "maintenance"))
        for data in notes_data:
            data = data.copy()
            data["updateddate"] = set_default_time(data["updateddate"])
            if "pubdate" in data:
                data["pubdate"] = set_default_time(data["pubdate"])
            feed.add_item(**data)
        result = feed.writeString("utf-8")

        self.assert_xml_equal(result, expected)
