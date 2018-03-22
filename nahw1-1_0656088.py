import sys
import requests
import cv2
import pytesseract
import shutil
import numpy
import re
import getopt
import getpass
import texttable as tt
from PIL import Image, ImageFilter
from html.parser import HTMLParser

# shamely copy from https://github.com/schmijos/html-table-parser-python3/blob/3d2557ff20e4926cd22fc57c487d88ae1eb1b893/html_table_parser/parser.py
class HTMLTableParser(HTMLParser):
    """ This class serves as a html table parser. It is able to parse multiple
    tables which you feed in. You can access the result per .tables field.
    """
    def __init__(
        self,
        decode_html_entities=False,
        data_separator=' ',
    ):

        HTMLParser.__init__(self)

        self._parse_html_entities = decode_html_entities
        self._data_separator = data_separator

        self._in_td = False
        self._in_th = False
        self._current_table = []
        self._current_row = []
        self._current_cell = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        """ We need to remember the opening point for the content of interest.
        The other tags (<table>, <tr>) are only handled at the closing point.
        """
        if tag == 'td':
            self._in_td = True
        if tag == 'th':
            self._in_th = True

    def handle_data(self, data):
        """ This is where we save content to a cell """
        if self._in_td or self._in_th:
            self._current_cell.append(data.strip())

    def handle_charref(self, name):
        """ Handle HTML encoded characters """

        if self._parse_html_entities:
            self.handle_data(self.unescape('&#{};'.format(name)))

    def handle_endtag(self, tag):
        """ Here we exit the tags. If the closing tag is </tr>, we know that we
        can save our currently parsed cells to the current table as a row and
        prepare for a new row. If the closing tag is </table>, we save the
        current table and prepare for a new one.
        """
        if tag == 'td':
            self._in_td = False
        elif tag == 'th':
            self._in_th = False

        if tag in ['td', 'th']:
            final_cell = self._data_separator.join(self._current_cell).strip()
            self._current_row.append(final_cell)
            self._current_cell = []
        elif tag == 'tr':
            self._current_table.append(self._current_row)
            self._current_row = []
        elif tag == 'table':
            self.tables.append(self._current_table)
            self._current_table = []
# End shamely copy

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        def func(e):
            (key, value) = e
            return key == 'name' or key == 'value'
        if tag == 'input':
            filtered = list(filter(lambda k : k[0] in ['name', 'value'], attrs))
            dic = {}
            for key, value in filtered:
                dic[key] = value
            self.inputs.append(dic)

def getCaptchaResult():
    Valid_Result_Pattern = re.compile('^\d\d\d\d$')
    while True:
        request = requests.session()
        captcha_image = getCaptcha(request)
        result = ocr(captcha_image)
        if Valid_Result_Pattern.match(result):
            break
    return result, request

def getCaptcha(request):
    # initial session
    request.get("https://portal.nctu.edu.tw/captcha/pic.php")
    # get captcha image
    response = request.get("https://portal.nctu.edu.tw/captcha/pitctest/pic.php", stream=True)
    response.raw.decode_content = True
    return Image.open(response.raw)

def ocr(image):
    pil_image = image.convert('RGB')
    open_cv_image = numpy.array(pil_image)
    imgray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(imgray, 108, 255, 0)

    image = Image.fromarray(thresh)

    result = pytesseract.image_to_string(image, config='outputbase digits').replace(' ', '')
    return result

def login_portal(request, username, password, captcha):
    payload = {'username': username, 'password': password, 'seccode': captcha, 'pwdtype': 'static', 'Submit2': '(Login)'}
    response = request.post('https://portal.nctu.edu.tw/portal/chkpas.php?', data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if response.history:
        return
    else:
        raise Exception('Login failed')

def fetchRelayForm(request):
    response = request.get('https://portal.nctu.edu.tw/portal/relay.php?D=cos')
    response.encoding = 'big5'
    parser = MyHTMLParser()
    parser.feed(response.text)
    form = {}
    for input in parser.inputs:
        form[input['name']] = input['value'] if 'value' in input else ''
    return form

def login_course(request):
    form = fetchRelayForm(request)
    req = requests.Request('POST', 'https://course.nctu.edu.tw/jwt.asp', data=form)
    prepped = request.prepare_request(req)
    response = request.send(prepped)
    # response = request.post('https://course.nctu.edu.tw/index.asp', data=form)

    response.encoding = 'big5'
    if response.url == 'https://course.nctu.edu.tw/index.asp' and '驗證碼錯誤' in response.text:
        raise Exception('Login course failed!')
    return response

def download_schedule(request):
    response = request.get('https://course.nctu.edu.tw/adSchedule.asp')
    response.encoding = 'big5'
    if '無權限瀏覽' in response.text:
        raise Exception('Access denied!')
    return response

def draw_schedule(schedule):
    p = HTMLTableParser()
    p.feed(schedule)
    rows = p.tables[1]
    rows.pop(0)

    tab = tt.Texttable()

    # don't use vertical line beteew cols.
    tab.set_deco(tt.Texttable.HEADER + tt.Texttable.BORDER + tt.Texttable.VLINES)

    # set line below header as "-"
    tab.set_chars(['-', '|', '+', '-'])

    # set header text
    headings = ['節次', '時間\\星期', '(一)', '(二)', '(三)', '(四)', '(五)', '(六)', '(日)']
    tab.header(headings)

    # append table row
    for row in rows:
        tab.add_row(row)

    # print out table
    print(tab.draw())

def main():
    opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])

    for o, a in opts:
        if o in ("-h", "--help"):
            print("usage: nahw1-1_0656088.py [-h] username")
            print("")
            print("Web crawler for NCTU class schedule.")
            print("")
            print("positional arguments:")
            print("    username    username of NCTU portal")
            print("")
            print("optional arguments:")
            print("    -h, --help  show this help message and exit")
            sys.exit()
        else:
            assert False, "Unreconized options"

    student_id = args[-1]
    password = getpass.getpass("Portal Password:")
    captcha, request = getCaptchaResult()
    while True:
        try:
            login_portal(request = request, username = student_id, password = password, captcha = captcha)
            break
        except Exception:
            print('Cannot login, re-fetch captcha code and retry.')
            # cannot login, re-fetch captcha code and retry.
            captcha, request = getCaptchaResult()
            continue


    try:
        login_course(request)
    except Exception:
        print('[Fatel] Login course failed.')
        sys.exit()

    try:
        schedule_page = download_schedule(request).text
    except Exception:
        print('[Fatel] Schedule page access denied. Maybe exceed the limit of login.')
        sys.exit()

    draw_schedule(schedule_page)

if __name__ == "__main__":
    main()
