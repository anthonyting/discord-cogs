import os
import random
from typing import Callable, Iterable, List, Optional, cast
from icrawler.builtin import GoogleImageCrawler, GoogleParser, GoogleFeeder
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import sys
import logging

from icrawler import ImageDownloader

import re

import pexpect.popen_spawn

url_regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

def is_url(value: str, required_extension: Optional[List[str]] = None) -> bool:
    if url_regex.match(value) is not None:
        if required_extension is None:
            return True

        extension = os.path.splitext(value)[-1][1:].lower()
        if extension in required_extension:
            return True

    return False


class CustomDownloader(ImageDownloader):
    """Downloader specified for images."""

    def get_filename(self, task, default_ext, keyword):
        filename = super(ImageDownloader, self).get_filename(task, default_ext)
        return keyword

    def keep_file(self, task, response, **kwargs):
        return True

    def download(
        self, task, default_ext, timeout=5, max_retry=3, overwrite=False, **kwargs
    ):
        """Download the image and save it to the corresponding path.
        Args:
            task (dict): The task dict got from ``task_queue``.
            timeout (int): Timeout of making requests for downloading images.
            max_retry (int): the max retry times if the request fails.
            **kwargs: reserved arguments for overriding.
        """
        file_url = task["file_url"]
        task["success"] = False
        task["filename"] = None
        retry = max_retry
        keyword = kwargs["keyword"]

        # if not overwrite:
        # with self.lock:
        # self.fetched_num += 1
        # filename = self.get_filename(task, default_ext, keyword)
        # if self.storage.exists(filename):
        # self.logger.info('skip downloading file %s', filename)
        # return
        # self.fetched_num -= 1

        while retry > 0 and not self.signal.get("reach_max_num"):
            try:
                response = self.session.get(file_url, timeout=timeout)
            except Exception as e:
                self.logger.error(
                    "Exception caught when downloading file %s, "
                    "error: %s, remaining retry times: %d",
                    file_url,
                    e,
                    retry - 1,
                )
            else:
                if self.reach_max_num():
                    self.signal.set(reach_max_num=True)
                    break
                elif response.status_code != 200:
                    self.logger.error(
                        "Response status code %d, file %s",
                        response.status_code,
                        file_url,
                    )
                    break
                elif not self.keep_file(task, response, **kwargs):
                    break
                with self.lock:
                    self.fetched_num += 1
                    filename = self.get_filename(task, default_ext, keyword)
                self.logger.info("image #%s\t%s", self.fetched_num, file_url)
                self.storage.write(filename, response.content)
                task["success"] = True
                task["filename"] = filename
                break
            finally:
                retry -= 1


class CustomGoogleFeederSafe(GoogleFeeder):
    def feed(self, keyword, offset, max_num, language=None, filters=None):
        base_url = "https://www.google.com/search?"
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters, sep=",")
        for _ in range(offset, offset + max_num, 100):
            params = dict(
                q=keyword, tbs=filter_str, tbm="isch"
            )
            if language:
                params["lr"] = "lang_" + language
            url = base_url + urlencode(params) + "&safe=active"
            self.out_queue.put(url)
            self.logger.debug("put url to url_queue: {}".format(url))


class CustomGoogleFeeder(GoogleFeeder):
    def feed(self, keyword, offset, max_num, language=None, filters=None):
        base_url = "https://www.google.com/search?"
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters, sep=",")
        for _ in range(offset, offset + max_num, 100):
            params = dict(
                q=keyword, tbs=filter_str, tbm="isch"
            )
            if language:
                params["lr"] = "lang_" + language
            url = base_url + urlencode(params)
            self.out_queue.put(url)
            self.logger.debug("put url to url_queue: {}".format(url))


class JsTokenizer:
    def __init__(self) -> None:
        tokenize_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './tokenize/src/index.js')
        self._tokenizer = pexpect.popen_spawn.PopenSpawn(f"node {tokenize_script_path}")
        self._tokenizer.logfile = sys.stdout.buffer if logging.root.level == logging.DEBUG else None
        self._tokenizer.expect("STARTED TOKENIZER")
        self._tokenizer.delimiter = "DONE"  # type: ignore

    def get_strings(
        self, code: str, matcher: Optional[Callable[[str], bool]] = None
    ) -> Iterable[str]:
        self._tokenizer.send(str.encode(code, "utf-8"))
        output = self._tokenizer.read()

        if output:
            data = (
                cast(bytes, output).decode("utf-8")
                if type(output) == bytes
                else cast(str, output)
            )
            return filter(
                matcher, [value.strip('"') for value in data.split("\n")[0:-1]]
            )

        return []


class CustomGoogleParser(GoogleParser):
    def __init__(self, thread_num, signal, session):
        super().__init__(thread_num, signal, session)

        self.tokenizer = JsTokenizer()

    def parse(self, response):
        soup = BeautifulSoup(response.content.decode("utf-8", "ignore"), "lxml")
        script_tags = soup.find_all(name="script")

        urls = [
            {"file_url": url}
            for script in script_tags
            for url in self.tokenizer.get_strings(
                str(script), lambda string: is_url(string, ["jpg", "jpeg", "png"])
            )
        ]

        random.shuffle(urls)

        return urls


class CustomGoogleCrawler(GoogleImageCrawler):
    def crawl(
        self,
        keyword,
        filters=None,
        offset=0,
        max_num=1000,
        min_size=None,
        max_size=None,
        language=None,
        file_idx_offset=0,
        overwrite=False,
    ):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error(
                    '"Offset" cannot exceed 1000, otherwise you will get '
                    "duplicated searching results."
                )
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    "Due to Google's limitation, you can only get the first "
                    '1000 result. "max_num" has been automatically set to %d. '
                    "If you really want to get more than 1000 results, you "
                    "can specify different date ranges.",
                    1000 - offset,
                )

        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            language=language,
            filters=filters,
        )
        downloader_kwargs = dict(
            keyword=keyword,  # added line
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset,
            overwrite=overwrite,
        )
        super(GoogleImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs
        )
