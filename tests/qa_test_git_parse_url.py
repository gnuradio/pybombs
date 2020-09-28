#
# Copyright 2019,2020 Free Software Foundation, Inc.
#
# This file is part of PyBOMBS
#
# PyBOMBS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# PyBOMBS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBOMBS; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

# run as 'python -m unittest discover --start-directory=tests --pattern=qa_*.py'

import pybombs.fetchers.git as git
import unittest


class TestUrlParsing(unittest.TestCase):

    def do_git_parse_url(self, url_in, url_expected, gitrev):
        url_out, args = git.parse_git_url(url_in, {})
        self.assertEqual(url_out, url_expected)
        self.assertEqual(args.get('gitrev'), gitrev)

# check legal git URLs with and without pybombs [@commit] suffix
# https://git-scm.com/docs/git-clone/

####
# bare repos
####

# test SSH variants
# ssh://[user@]host.xz[:port]/path/to/repo.git[@commit]
    def test_ssh_0000(self): self.do_git_parse_url("ssh://host.xz/path/to/pybombs.git", "ssh://host.xz/path/to/pybombs.git", None)
    def test_ssh_u000(self): self.do_git_parse_url("ssh://user@host.xz/path/to/pybombs.git", "ssh://user@host.xz/path/to/pybombs.git", None)
    def test_ssh_00p0(self): self.do_git_parse_url("ssh://host.xz:234/path/to/pybombs.git", "ssh://host.xz:234/path/to/pybombs.git", None)
    def test_ssh_000c(self): self.do_git_parse_url("ssh://host.xz/path/to/pybombs.git@_Commit-0", "ssh://host.xz/path/to/pybombs.git", "_Commit-0")
    def test_ssh_u0p0(self): self.do_git_parse_url("ssh://user@host.xz:234/path/to/pybombs.git", "ssh://user@host.xz:234/path/to/pybombs.git", None)
    def test_ssh_00pc(self): self.do_git_parse_url("ssh://host.xz:234/path/to/pybombs.git@_Commit-0", "ssh://host.xz:234/path/to/pybombs.git", "_Commit-0")
    def test_ssh_u00c(self): self.do_git_parse_url("ssh://user@host.xz/path/to/pybombs.git@_Commit-0", "ssh://user@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_ssh_u0pc(self): self.do_git_parse_url("ssh://user@host.xz:234/path/to/pybombs.git@_Commit-0", "ssh://user@host.xz:234/path/to/pybombs.git", "_Commit-0")

    def test_gpssh_0000(self): self.do_git_parse_url("git+ssh://host.xz/path/to/pybombs.git", "git+ssh://host.xz/path/to/pybombs.git", None)
    def test_gpssh_u000(self): self.do_git_parse_url("git+ssh://user@host.xz/path/to/pybombs.git", "git+ssh://user@host.xz/path/to/pybombs.git", None)  # FAIL under 2.3.4a0
    def test_gpssh_ut00(self): self.do_git_parse_url("git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", None)  # FAIL under 2.3.4a0
    def test_gpssh_000c(self): self.do_git_parse_url("git+ssh://host.xz/path/to/pybombs.git@_Commit-0", "git+ssh://host.xz/path/to/pybombs.git", "_Commit-0")
    def test_gpssh_u00c(self): self.do_git_parse_url("git+ssh://user@host.xz/path/to/pybombs.git@_Commit-0", "git+ssh://user@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_gpssh_ut0c(self): self.do_git_parse_url("git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git@_Commit-0", "git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "_Commit-0")

    # test using tokens
    def test_ssh_ut00(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", None)  # FAIL under 2.3.4a0
    def test_ssh_utp0(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", None)
    def test_ssh_ut0c(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git@_Commit-0", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_ssh_utpc(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git@_Commit-0", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", "_Commit-0")

# test git & ftp protocol variants
# git://host.xz[:port]/path/to/repo.git/
# ftp[s]://host.xz[:port]/path/to/repo.git/
    def test_git_0000(self): self.do_git_parse_url("git://host.xz/path/to/pybombs.git", "git://host.xz/path/to/pybombs.git", None)
    def test_git_00p0(self): self.do_git_parse_url("git://host.xz:234/path/to/pybombs.git", "git://host.xz:234/path/to/pybombs.git", None)
    def test_git_000c(self): self.do_git_parse_url("git://host.xz/path/to/pybombs.git@_Commit-0", "git://host.xz/path/to/pybombs.git", "_Commit-0")
    def test_git_00pc(self): self.do_git_parse_url("git://host.xz:234/path/to/pybombs.git@_Commit-0", "git://host.xz:234/path/to/pybombs.git", "_Commit-0")

    # test using tokens
    def test_git_u000(self): self.do_git_parse_url("git://user@host.xz/path/to/pybombs.git", "git://user@host.xz/path/to/pybombs.git", None)
    def test_git_u0p0(self): self.do_git_parse_url("git://user@host.xz:234/path/to/pybombs.git", "git://user@host.xz:234/path/to/pybombs.git", None)
    def test_git_u00c(self): self.do_git_parse_url("git://user@host.xz/path/to/pybombs.git@_Commit-0", "git://user@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_git_u0pc(self): self.do_git_parse_url("git://user@host.xz:234/path/to/pybombs.git@_Commit-0", "git://user@host.xz:234/path/to/pybombs.git", "_Commit-0")
    def test_git_ut00(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", None)  # FAIL under 2.3.4a0
    def test_git_utp0(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", None)
    def test_git_ut0c(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git@_Commit-0", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_git_utpc(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git@_Commit-0", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", "_Commit-0")

# test http[s] protocol variants
# https://host.xz[:port]/path/to/repo.git/
    def test_http_0000(self): self.do_git_parse_url("https://host.xz/path/to/pybombs.git", "https://host.xz/path/to/pybombs.git", None)
    def test_http_00p0(self): self.do_git_parse_url("https://host.xz:234/path/to/pybombs.git", "https://host.xz:234/path/to/pybombs.git", None)
    def test_http_000c(self): self.do_git_parse_url("https://host.xz/path/to/pybombs.git@_Commit-0", "https://host.xz/path/to/pybombs.git", "_Commit-0")
    def test_http_00pc(self): self.do_git_parse_url("https://host.xz:234/path/to/pybombs.git@_Commit-0", "https://host.xz:234/path/to/pybombs.git", "_Commit-0")

    def test_gphttp_0000(self): self.do_git_parse_url("git+https://host.xz/path/to/pybombs.git", "git+https://host.xz/path/to/pybombs.git", None)
    def test_gphttp_000c(self): self.do_git_parse_url("git+https://host.xz/path/to/pybombs.git@_Commit-0", "git+https://host.xz/path/to/pybombs.git", "_Commit-0")

    # test using tokens
    def test_http_u000(self): self.do_git_parse_url("https://user@host.xz/path/to/pybombs.git", "https://user@host.xz/path/to/pybombs.git", None)
    def test_http_u0p0(self): self.do_git_parse_url("https://user@host.xz:234/path/to/pybombs.git", "https://user@host.xz:234/path/to/pybombs.git", None)
    def test_http_u00c(self): self.do_git_parse_url("https://user@host.xz/path/to/pybombs.git@_Commit-0", "https://user@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_http_u0pc(self): self.do_git_parse_url("https://user@host.xz:234/path/to/pybombs.git@_Commit-0", "https://user@host.xz:234/path/to/pybombs.git", "_Commit-0")
    def test_http_ut00(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", None)  # FAIL under 2.3.4a0
    def test_http_utp0(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", None)
    def test_http_ut0c(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git@_Commit-0", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_http_utpc(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git@_Commit-0", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs.git", "_Commit-0")

    def test_gphttp_u000(self): self.do_git_parse_url("git+https://user@host.xz/path/to/pybombs.git", "git+https://user@host.xz/path/to/pybombs.git", None)  # FAIL under 2.3.4a0
    def test_gphttp_ut00(self): self.do_git_parse_url("git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", None)  # FAIL under 2.3.4a0
    def test_gphttp_u00c(self): self.do_git_parse_url("git+https://user@host.xz/path/to/pybombs.git@_Commit-0", "git+https://user@host.xz/path/to/pybombs.git", "_Commit-0")
    def test_gphttp_ut0c(self): self.do_git_parse_url("git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git@_Commit-0", "git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs.git", "_Commit-0")

# test scp-like syntax
# [user@]host.xz:path/to/repo.git/
    def test_scp_0000(self): self.do_git_parse_url("host.xz:path/to/pybombs.git", "host.xz:path/to/pybombs.git", None)
    def test_scp_u000(self): self.do_git_parse_url("user@host.xz:path/to/pybombs.git", "user@host.xz:path/to/pybombs.git", None)
    def test_scp_000c(self): self.do_git_parse_url("host.xz:path/to/pybombs.git@_Commit-0", "host.xz:path/to/pybombs.git", "_Commit-0")
    def test_scp_u00c(self): self.do_git_parse_url("user@host.xz:path/to/pybombs.git@_Commit-0", "user@host.xz:path/to/pybombs.git", "_Commit-0")

# test local git repos
# /path/to/repo.git/
# file:///path/to/repo.git/
    def test_local_0000(self): self.do_git_parse_url("/path/to/pybombs.git", "/path/to/pybombs.git", None)
    def test_local_000c(self): self.do_git_parse_url("/path/to/pybombs.git@_Commit-0", "/path/to/pybombs.git", "_Commit-0")
    def test_file_0000(self): self.do_git_parse_url("file:///path/to/pybombs.git", "file:///path/to/pybombs.git", None)
    def test_file_000c(self): self.do_git_parse_url("file:///path/to/pybombs.git@_Commit-0", "file:///path/to/pybombs.git", "_Commit-0")

####
# non-bare repos
####

# test SSH variants
# ssh://[user@]host.xz[:port]/path/to/repo.git[@commit]
    def test_nbssh_0000(self): self.do_git_parse_url("ssh://host.xz/path/to/pybombs", "ssh://host.xz/path/to/pybombs", None)
    def test_nbssh_u000(self): self.do_git_parse_url("ssh://user@host.xz/path/to/pybombs", "ssh://user@host.xz/path/to/pybombs", None)
    def test_nbssh_00p0(self): self.do_git_parse_url("ssh://host.xz:234/path/to/pybombs", "ssh://host.xz:234/path/to/pybombs", None)
    def test_nbssh_000c(self): self.do_git_parse_url("ssh://host.xz/path/to/pybombs@_Commit-0", "ssh://host.xz/path/to/pybombs", "_Commit-0")
    def test_nbssh_u0p0(self): self.do_git_parse_url("ssh://user@host.xz:234/path/to/pybombs", "ssh://user@host.xz:234/path/to/pybombs", None)
    def test_nbssh_00pc(self): self.do_git_parse_url("ssh://host.xz:234/path/to/pybombs@_Commit-0", "ssh://host.xz:234/path/to/pybombs", "_Commit-0")
    def test_nbssh_u00c(self): self.do_git_parse_url("ssh://user@host.xz/path/to/pybombs@_Commit-0", "ssh://user@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbssh_u0pc(self): self.do_git_parse_url("ssh://user@host.xz:234/path/to/pybombs@_Commit-0", "ssh://user@host.xz:234/path/to/pybombs", "_Commit-0")

    def test_nbgpssh_0000(self): self.do_git_parse_url("git+ssh://host.xz/path/to/pybombs", "git+ssh://host.xz/path/to/pybombs", None)
    def test_nbgpssh_u000(self): self.do_git_parse_url("git+ssh://user@host.xz/path/to/pybombs", "git+ssh://user@host.xz/path/to/pybombs", None)  # FAIL under 2.3.4a0
    def test_nbgpssh_ut00(self): self.do_git_parse_url("git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", None)  # FAIL under 2.3.4a0
    def test_nbgpssh_000c(self): self.do_git_parse_url("git+ssh://host.xz/path/to/pybombs@_Commit-0", "git+ssh://host.xz/path/to/pybombs", "_Commit-0")
    def test_nbgpssh_u00c(self): self.do_git_parse_url("git+ssh://user@host.xz/path/to/pybombs@_Commit-0", "git+ssh://user@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbgpssh_ut0c(self): self.do_git_parse_url("git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs@_Commit-0", "git+ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "_Commit-0")

    # test using tokens
    def test_nbssh_ut00(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", None)  # FAIL under 2.3.4a0
    def test_nbssh_utp0(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", None)
    def test_nbssh_ut0c(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs@_Commit-0", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbssh_utpc(self): self.do_git_parse_url("ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs@_Commit-0", "ssh://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", "_Commit-0")

# test git & ftp protocol variants
# git://host.xz[:port]/path/to/repo.git/
# ftp[s]://host.xz[:port]/path/to/repo.git/
    def test_nbgit_0000(self): self.do_git_parse_url("git://host.xz/path/to/pybombs", "git://host.xz/path/to/pybombs", None)
    def test_nbgit_00p0(self): self.do_git_parse_url("git://host.xz:234/path/to/pybombs", "git://host.xz:234/path/to/pybombs", None)
    def test_nbgit_000c(self): self.do_git_parse_url("git://host.xz/path/to/pybombs@_Commit-0", "git://host.xz/path/to/pybombs", "_Commit-0")
    def test_nbgit_00pc(self): self.do_git_parse_url("git://host.xz:234/path/to/pybombs@_Commit-0", "git://host.xz:234/path/to/pybombs", "_Commit-0")

    # test using tokens
    def test_nbgit_u000(self): self.do_git_parse_url("git://user@host.xz/path/to/pybombs", "git://user@host.xz/path/to/pybombs", None)
    def test_nbgit_u0p0(self): self.do_git_parse_url("git://user@host.xz:234/path/to/pybombs", "git://user@host.xz:234/path/to/pybombs", None)
    def test_nbgit_u00c(self): self.do_git_parse_url("git://user@host.xz/path/to/pybombs@_Commit-0", "git://user@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbgit_u0pc(self): self.do_git_parse_url("git://user@host.xz:234/path/to/pybombs@_Commit-0", "git://user@host.xz:234/path/to/pybombs", "_Commit-0")
    def test_nbgit_ut00(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", None)  # FAIL under 2.3.4a0
    def test_nbgit_utp0(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", None)
    def test_nbgit_ut0c(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs@_Commit-0", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbgit_utpc(self): self.do_git_parse_url("git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs@_Commit-0", "git://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", "_Commit-0")

# test http[s] protocol variants
# https://host.xz[:port]/path/to/repo.git/
    def test_nbhttp_0000(self): self.do_git_parse_url("https://host.xz/path/to/pybombs", "https://host.xz/path/to/pybombs", None)
    def test_nbhttp_00p0(self): self.do_git_parse_url("https://host.xz:234/path/to/pybombs", "https://host.xz:234/path/to/pybombs", None)
    def test_nbhttp_000c(self): self.do_git_parse_url("https://host.xz/path/to/pybombs@_Commit-0", "https://host.xz/path/to/pybombs", "_Commit-0")
    def test_nbhttp_00pc(self): self.do_git_parse_url("https://host.xz:234/path/to/pybombs@_Commit-0", "https://host.xz:234/path/to/pybombs", "_Commit-0")

    def test_nbgphttp_0000(self): self.do_git_parse_url("git+https://host.xz/path/to/pybombs", "git+https://host.xz/path/to/pybombs", None)
    def test_nbgphttp_000c(self): self.do_git_parse_url("git+https://host.xz/path/to/pybombs@_Commit-0", "git+https://host.xz/path/to/pybombs", "_Commit-0")

    # test using tokens
    def test_nbhttp_u000(self): self.do_git_parse_url("https://user@host.xz/path/to/pybombs", "https://user@host.xz/path/to/pybombs", None)
    def test_nbhttp_u0p0(self): self.do_git_parse_url("https://user@host.xz:234/path/to/pybombs", "https://user@host.xz:234/path/to/pybombs", None)
    def test_nbhttp_u00c(self): self.do_git_parse_url("https://user@host.xz/path/to/pybombs@_Commit-0", "https://user@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbhttp_u0pc(self): self.do_git_parse_url("https://user@host.xz:234/path/to/pybombs@_Commit-0", "https://user@host.xz:234/path/to/pybombs", "_Commit-0")
    def test_nbhttp_ut00(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", None)  # FAIL under 2.3.4a0
    def test_nbhttp_utp0(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", None)
    def test_nbhttp_ut0c(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs@_Commit-0", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbhttp_utpc(self): self.do_git_parse_url("https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs@_Commit-0", "https://user:ToKeN2-._~!$&'()*+,;=@host.xz:234/path/to/pybombs", "_Commit-0")

    def test_nbgphttp_u000(self): self.do_git_parse_url("git+https://user@host.xz/path/to/pybombs", "git+https://user@host.xz/path/to/pybombs", None)  # FAIL under 2.3.4a0
    def test_nbgphttp_ut00(self): self.do_git_parse_url("git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", None)  # FAIL under 2.3.4a0
    def test_nbgphttp_u00c(self): self.do_git_parse_url("git+https://user@host.xz/path/to/pybombs@_Commit-0", "git+https://user@host.xz/path/to/pybombs", "_Commit-0")
    def test_nbgphttp_ut0c(self): self.do_git_parse_url("git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs@_Commit-0", "git+https://user:ToKeN2-._~!$&'()*+,;=@host.xz/path/to/pybombs", "_Commit-0")

# test scp-like syntax
# [user@]host.xz:path/to/repo.git/
    def test_nbscp_0000(self): self.do_git_parse_url("host.xz:path/to/pybombs", "host.xz:path/to/pybombs", None)
    def test_nbscp_u000(self): self.do_git_parse_url("user@host.xz:path/to/pybombs", "user@host.xz:path/to/pybombs", None)
    def test_nbscp_000c(self): self.do_git_parse_url("host.xz:path/to/pybombs@_Commit-0", "host.xz:path/to/pybombs", "_Commit-0")
    def test_nbscp_u00c(self): self.do_git_parse_url("user@host.xz:path/to/pybombs@_Commit-0", "user@host.xz:path/to/pybombs", "_Commit-0")

# test local git repos
# /path/to/repo.git/
# file:///path/to/repo.git/
    def test_nblocal_0000(self): self.do_git_parse_url("/path/to/pybombs", "/path/to/pybombs", None)
    def test_nblocal_000c(self): self.do_git_parse_url("/path/to/pybombs@_Commit-0", "/path/to/pybombs", "_Commit-0")
    def test_nbfile_0000(self): self.do_git_parse_url("file:///path/to/pybombs", "file:///path/to/pybombs", None)
    def test_nbfile_000c(self): self.do_git_parse_url("file:///path/to/pybombs@_Commit-0", "file:///path/to/pybombs", "_Commit-0")


if __name__ == '__main__':
    unittest.main()
