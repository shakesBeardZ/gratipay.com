# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from gratipay.testing import Harness

from gratipay import clean_npm


class ScrubNPMDescriptionTests(Harness):

    def test_returns_None_if_no_pkg_name(self):
        assert clean_npm.get_npm_description('') is None

    def test_returns_None_if_pkg_doesnt_exist(self):
        assert clean_npm.get_npm_description('kaskhja') is None

    def test_returns_None_if_no_description(self):
        assert clean_npm.scrub_description(None) is None

    def test_returns_clean_description(self):
        raw_description = """This package was published as a result of a bug, please use the &lt;a href&#x3D;&quot;https://www.npmjs.com/package/express&quot;&gt;express&lt;/a&gt; package instead."""
        clean_description = """This package was published as a result of a bug, please use the  package instead."""
        assert clean_npm.scrub_description(raw_description) == clean_description

    def test_correct_no_pkgs_to_clean(self):

        self.make_package()
        self.make_package(name='foo1', description='Foo1 fooingly.'emails=['alice1@example.com'])
        self.make_package(name='foo2', description='Foo2 fooingly.'emails=['alice2@example.com'])
        assert len(clean_npm.get_dirty_packages(self.db)) == 3

    def test_description_dirty_changed_on_clean(self):
        pass

    def test_description_dirty_changed_on_sync_npm(self):
        pass
