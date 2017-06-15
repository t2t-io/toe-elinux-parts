#!/usr/bin/env python3
#
# coding=utf-8
#
# -------------------------------------------------------------------------
# Copyright 2014-2015 T2T Inc. All rights reserved.
#
# FILE:
#     tic.py
#
# DESCRIPTION:
#     Cloud service helpers for T-T-T
#
#
# REVISION HISTORY
#     2017/02/03, yagamy, initial version.
#
#
# -------------------------------------------------------------------------
#
import os
import sys
import traceback
import json
from os.path import isfile, basename, dirname
from tempfile import NamedTemporaryFile
import shutil

from httpie_utils import http_cli, StrCLIResponse, BytesCLIResponse
import ruamel.yaml
from colorama import Fore, Back, Style


class TicManager:
    def __init__(self, config_file, logger):
        self._config_file = config_file
        self._logger = logger
        self.load_configs()


    def load_configs(self):
        logger = self._logger
        try:
            if not isfile(self._config_file):
                logger.error("no such file: %s" % (self._config_file))
                sys.exit(1)
                return
            content = open(self._config_file, 'r').read()
            config = ruamel.yaml.load(content, Loader=ruamel.yaml.Loader)
            self._config = config
            self._release_server_url = self.read_config('release-server/url')
            self._release_server_user = self.read_config('release-server/user')
            self._release_server_pswd = self.read_config('release-server/password')
            self._archive_server_url = self.read_config('archive-server/url')
            self._file_collector_url = self.read_config('file-server/fc')
            self._file_collector_user = self.read_config('file-server/publish-user')
            self._file_collector_pswd = self.read_config('file-server/publish-password')
            self._fc_release_site = self.read_config('file-server/release-site')
            self._fc_archive_site = self.read_config('file-server/archive-site')
            self._fc_file_site = self.read_config('file-server/file-site')
            self._fc_sites = {
                'release': self._fc_release_site,
                'archive': self._fc_archive_site,
                'file'   : self._fc_file_site
            }
        except Exception as ex:
            print(traceback.format_exc())
            sys.exit(1)


    def read_config(self, path):
        logger = self._logger
        config = self._config
        tokens = path.split('/')
        for t in tokens:
            config = config[t]
            if config is None:
                logger.warn("missing %s in %s" % (path, self._config_file))
                sys.exit(2)
        logger.debug("loading %s ... => %s" % (path, config))
        return config


    def list_release_files(self, path, fullpath=False):
        path = "%s/" % path if path[-1] != '/' else path
        pattern = "%s%s" if self._release_server_url[-1] == '/' else "%s/%s"
        url = pattern % (self._release_server_url, path)
        try:
            r = http_cli(
                '-a',
                "%s:%s" % (self._release_server_user, self._release_server_pswd),
                '--check-status',
                '--ignore-stdin',
                '--follow',
                url
            )
            if type(r) == StrCLIResponse and r.exit_status == 0 and r.json is not None:
                xs = [ x['name'] for x in r.json ]
                xs = [ "%s%s" % (url, x) for x in xs ] if fullpath else xs
                return xs
        except Exception as e:
            print(traceback.format_exc())
            sys.exit(2)


    def submit_dummy_json(self, path):
        logger = self._logger
        path = path[:-1] if path[-1] == '/' else path
        try:
            f = NamedTemporaryFile(delete=False, mode='w')
            f.write(json.dumps({'dummy': True}))
            f.close()
            logger.debug("upload_dummy_json: temp-file for dummy.json: %s" % (f.name))
            r = http_cli(
                '-a',
                "%s:%s" % (self._file_collector_user, self._file_collector_pswd),
                '--check-status',
                '--ignore-stdin',
                "%s/api/v1/c/submit" % (self._file_collector_url),
                "site=%s" % (self._fc_release_site),
                "overwrite=true",
                "content:=@%s" % (f.name),
                "fullpath=%s/_dummy" % (path)
            )
            if type(r) == StrCLIResponse and r.exit_status == 0 and r.json is not None:
                logger.debug("upload_dummy_json: r.json => %s" % (r.json))
                logger.info("upload %s/_dummy.json successfully" % (path))
                return
            else:
                logger.error("upload_dummy_json: unexpected error when uploading dummy json for %s" % (path))
                logger.error("upload_dummy_json: r.exit_status: %d" % (r.exit_status))
                sys.exit(3)
        except Exception as e:
            print(traceback.format_exc())
            sys.exit(2)


    def upload_file(self, site, directory, content_path):
        if not site in self._fc_sites:
            raise Exception("missing %s site in TicManager" % (site))
        site_domain_name = self._fc_sites[site]
        return http_cli(
                '-a',
                "%s:%s" % (self._file_collector_user, self._file_collector_pswd),
                '--check-status',
                '--ignore-stdin',
                '--form',
                "%s/api/v1/c/upload" % (self._file_collector_url),
                "site=%s" % (site_domain_name),
                "overwrite=true",
                "content@%s" % (content_path),
                "directory=%s" % (directory)
            )


    def publish_file(self, src, fullpath, chains=[], chained=False):
        logger = self._logger
        fullpath = fullpath[1:] if fullpath[0] == '/' else fullpath
        path = dirname(fullpath)
        name = basename(fullpath)
        tmp = "/tmp/%s" % (name)
        logger.debug("copying %s to %s" % (src, tmp))
        try:
            if not chained:
                shutil.copyfile(src, tmp)
                logger.info("copied %s successfully" % (tmp))
            r = self.upload_file(
                    'release',
                    path,
                    tmp
                )
            if type(r) == StrCLIResponse and r.exit_status == 0 and r.json is not None:
                logger.debug("publish_file: r.json => %s" % (r.json))
                logger.info("publish successfully => %s%s/%s%s" % (Fore.GREEN, self._release_server_url, fullpath, Style.RESET_ALL))
                [ m.publish_file(src, fullpath, [], True) for m in chains ]
                if not chained:
                    os.remove(tmp)
                    logger.info("successfully remove %s" % (tmp))
                return
            else:
                logger.error("publish_file: unexpected error when uploading dummy json for %s" % (path))
                logger.error("publish_file: r.exit_status: %d" % (r.exit_status))
                sys.exit(3)
        except Exception as e:
            print(traceback.format_exc())
            sys.exit(2)

