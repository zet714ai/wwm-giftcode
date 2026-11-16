import re
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup


BLACKLIST_WORDS = {
    "ACTIVE",
    "ANDROID",
    "AUGUST",
    "CANCEL",
    "CODE",
    "CODES",
    "CONFIRM",
    "DECEMBER",
    "DISCORD",
    "EXPIRED",
    "FACEBOOK",
    "FEBRUARY",
    "FANDOM",
    "FRIDAY",
    "GLOBAL",
    "INACTIVE",
    "JANUARY",
    "JULY",
    "JUNE",
    "MARCH",
    "MOBILE",
    "MONDAY",
    "NOVEMBER",
    "OCTOBER",
    "POLICY",
    "PRIVACY",
    "PROMO",
    "REDDIT",
    "RELEASE",
    "REWARD",
    "REWARDS",
    "SATURDAY",
    "SEARCH",
    "SEPTEMBER",
    "SERVER",
    "SIGNUP",
    "SOURCE",
    "STEAM",
    "SUNDAY",
    "TERMS",
    "THURSDAY",
    "TUESDAY",
    "UPDATE",
    "VERSION",
    "WEDNESDAY",
    "WIKI",
    "WINDOWS",
    "YOUTUBE",
}

CODE_PATTERN = re.compile(r"\b[A-Za-z0-9]{6,20}\b")
HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
ACTIVE_MARKERS = ("active code", "active gift", "mã đang hoạt động", "mã còn hạn")
EXPIRED_MARKERS = (
    "expired code",
    "expired gift",
    "inactive code",
    "mã hết hạn",
    "mã đã hết hạn",
    "code cũ",
)


class ScraperService:
    def __init__(self, data_manager):
        self.dm = data_manager
        self.headers = {
            "User-Agent": "WWMGiftcodeTool/1.0 (personal use)"
        }

    def fetch_from_urls(self, url_list):
        aggregated_codes = {}
        report_lines = []
        successful_pages = 0
        valid_url_count = 0

        for raw_url in url_list:
            url = raw_url.strip()
            if not url:
                continue
            if not self.dm.validate_url(url):
                report_lines.append(f"URL không hợp lệ, bỏ qua: {url}")
                continue

            valid_url_count += 1
            domain = urlparse(url).netloc
            try:
                parsed_url = urlparse(url)
                if self._is_mediawiki_article_url(parsed_url):
                    page_html = self._fetch_mediawiki_article(url)
                elif parsed_url.path.rstrip("/").endswith("/api.php"):
                    page_html = self._fetch_mediawiki_api_url(url)
                else:
                    response = requests.get(url, headers=self.headers, timeout=12)
                    response.raise_for_status()
                    page_html = response.text
            except requests.exceptions.RequestException as exc:
                report_lines.append(f"{domain}: Lỗi kết nối ({type(exc).__name__})")
                continue
            except ValueError as exc:
                report_lines.append(f"{domain}: Không đọc được API ({exc})")
                continue

            try:
                codes = self._extract_codes_from_html(page_html)
            except (TypeError, ValueError) as exc:
                report_lines.append(f"{domain}: Không đọc được nội dung ({exc})")
                continue

            successful_pages += 1
            report_lines.append(f"{domain}: Tìm thấy {len(codes)} mã tiềm năng")
            for code in codes:
                aggregated_codes.setdefault(code, set()).add(domain)

        new_count, existing_count = self.dm.add_codes_with_sources(
            {code: sorted(sources) for code, sources in aggregated_codes.items()}
        )
        summary = (
            f"Kết quả quét: {successful_pages}/{valid_url_count} trang đọc được.\n"
            + ("\n".join(report_lines) if report_lines else "Chưa có URL nào được cấu hình.")
            + f"\n\nTổng mã tiềm năng sau khi gộp trùng: {len(aggregated_codes)}."
            + f"\nMã mới thêm: {new_count}."
            + f"\nMã đã có, đã cập nhật nguồn: {existing_count}."
            + "\nLưu ý: mã cào được là mã tiềm năng; cần thử trong game để xác nhận."
        )
        return successful_pages > 0, summary

    @staticmethod
    def _is_mediawiki_article_url(parsed_url):
        return (
            parsed_url.hostname is not None
            and parsed_url.hostname.casefold().endswith("fandom.com")
            and "/wiki/" in parsed_url.path
        )

    def _fetch_mediawiki_article(self, article_url):
        parsed_url = urlparse(article_url)
        page_title = unquote(parsed_url.path.split("/wiki/", 1)[1]).replace("_", " ")
        if not page_title:
            raise ValueError("URL MediaWiki không có tên trang sau /wiki/.")
        api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/api.php"
        return self._request_mediawiki_parse(api_url, page_title)

    def _fetch_mediawiki_api_url(self, api_url):
        parsed_url = urlparse(api_url)
        query = parse_qs(parsed_url.query)
        page_title = query.get("page", [None])[0]
        if not page_title:
            raise ValueError(
                "URL api.php cần có tham số page=...; hoặc nhập URL bài viết dạng /wiki/Tên_trang."
            )
        endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        return self._request_mediawiki_parse(endpoint, page_title, query)

    def _request_mediawiki_parse(self, api_url, page_title, existing_params=None):
        params = {
            key: values[-1]
            for key, values in (existing_params or {}).items()
            if values
        }
        params.update(
            {
                "action": "parse",
                "page": page_title,
                "prop": "text",
                "format": "json",
            }
        )
        response = requests.get(
            api_url,
            params=params,
            headers=self.headers,
            timeout=12,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("API không trả về JSON hợp lệ.") from exc

        if not isinstance(payload, dict):
            raise ValueError("Cấu trúc phản hồi API không hợp lệ.")
        if "error" in payload:
            error = payload["error"]
            if isinstance(error, dict):
                message = error.get("info", error.get("code", "Lỗi API"))
            else:
                message = str(error)
            raise ValueError(message)

        parsed_page = payload.get("parse")
        if not isinstance(parsed_page, dict):
            raise ValueError("JSON không chứa dữ liệu parse của trang.")
        rendered = parsed_page.get("text", {})
        if isinstance(rendered, dict):
            rendered = rendered.get("*", "")
        if not isinstance(rendered, str) or not rendered.strip():
            raise ValueError("API không trả về nội dung bài viết đã phân tích.")
        return rendered

    @classmethod
    def _extract_codes_from_html(cls, html_text):
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(("script", "style", "nav", "footer", "header", "aside", "noscript")):
            tag.decompose()

        content = soup.select_one(".mw-parser-output") or soup.find("main") or soup
        headings = content.find_all(HEADING_TAGS)
        active_headings = [
            heading
            for heading in headings
            if cls._contains_marker(heading.get_text(" ", strip=True), ACTIVE_MARKERS)
            and not cls._contains_marker(heading.get_text(" ", strip=True), EXPIRED_MARKERS)
        ]

        candidates = []
        if active_headings:
            for heading in active_headings:
                candidates.extend(cls._section_candidates(heading, content))
        else:
            excluded = cls._expired_section_elements(headings)
            candidates = [
                element
                for element in content.find_all(["code", "strong", "b", "td", "li", "p"])
                if element not in excluded
            ]

        codes = []
        for element in candidates:
            for match in CODE_PATTERN.findall(element.get_text(" ", strip=True)):
                code = match.upper()
                if cls._is_likely_code(code):
                    codes.append(code)
        return list(dict.fromkeys(codes))

    @classmethod
    def _section_candidates(cls, heading, content):
        candidates = []
        level = int(heading.name[1])
        for element in heading.find_all_next():
            if element is content:
                continue
            if element.name in HEADING_TAGS and int(element.name[1]) <= level:
                break
            if element.name in {"code", "strong", "b", "td", "li", "p"}:
                candidates.append(element)
        return candidates

    @classmethod
    def _expired_section_elements(cls, headings):
        excluded = set()
        for heading in headings:
            if not cls._contains_marker(heading.get_text(" ", strip=True), EXPIRED_MARKERS):
                continue
            level = int(heading.name[1])
            for element in heading.find_all_next():
                if element.name in HEADING_TAGS and int(element.name[1]) <= level:
                    break
                excluded.add(element)
        return excluded

    @staticmethod
    def _contains_marker(text, markers):
        normalized = text.casefold()
        return any(marker in normalized for marker in markers)

    @staticmethod
    def _is_likely_code(token):
        return (
            token not in BLACKLIST_WORDS
            and any(character.isalpha() for character in token)
        )
