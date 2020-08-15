from icrawler.builtin import GoogleImageCrawler, GoogleParser, GoogleFeeder
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode

class CustomGoogleFeeder(GoogleFeeder):

    def feed(self, keyword, offset, max_num, language=None, filters=None):
        base_url = 'https://www.google.com/search?'
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters, sep=',')
        for i in range(offset, offset + max_num, 100):
            params = dict(
                q=keyword,
                ijn=int(i / 100),
                start=i,
                tbs=filter_str,
                tbm='isch')
            if language:
                params['lr'] = 'lang_' + language
            url = base_url + urlencode(params) + "&safe=active"
            self.out_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class CustomGoogleParser(GoogleParser):
    def parse(self, response):
        soup = BeautifulSoup(
            response.content.decode('utf-8', 'ignore'), 'lxml')
        #image_divs = soup.find_all('script')
        image_divs = soup.find_all(name='script')
        for div in image_divs:
            #txt = div.text
            txt = str(div)
            #if not txt.startswith('AF_initDataCallback'):
            if 'AF_initDataCallback' not in txt:
                continue
            if 'ds:0' in txt or 'ds:1' not in txt:
                continue
            #txt = re.sub(r"^AF_initDataCallback\({.*key: 'ds:(\d)'.+data:function\(\){return (.+)}}\);?$",
            #             "\\2", txt, 0, re.DOTALL)
            #meta = json.loads(txt)
            #data = meta[31][0][12][2]
            #uris = [img[1][3][0] for img in data if img[0] == 1]
            
            uris = re.findall(r'http.*?\.(?:jpg|png|bmp)', txt)
            return [{'file_url': uri} for uri in uris]

class CustomGoogleCrawler(GoogleImageCrawler):

    def crawl(self,
              keyword,
              filters=None,
              offset=0,
              max_num=1000,
              min_size=None,
              max_size=None,
              language=None,
              file_idx_offset=0,
              overwrite=False):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error(
                    '"Offset" cannot exceed 1000, otherwise you will get '
                    'duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    'Due to Google\'s limitation, you can only get the first '
                    '1000 result. "max_num" has been automatically set to %d. '
                    'If you really want to get more than 1000 results, you '
                    'can specify different date ranges.', 1000 - offset)

        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            language=language,
            filters=filters)
        downloader_kwargs = dict(
            keyword=keyword, # added line
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset,
            overwrite=overwrite)
        super(GoogleImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)