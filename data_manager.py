import copy
import json
import os
from urllib.parse import urlparse


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wwm_database.json")
DEFAULT_URLS = ["https://where-winds-meet.fandom.com/wiki/Promotional_Codes"]

DEFAULT_DATA = {
    "coords": {
        "open_btn": None,
        "input_box": None,
        "confirm_btn": None,
        "modal_color": None,
    },
    "delay": 2.5,
    "urls": DEFAULT_URLS,
    "code_pool": {},
    "all_codes": [],
    "accounts": {
        "Account 1": {
            "used_codes": [],
        }
    },
    "last_account": "Account 1",
}


class DataManager:
    def __init__(self):
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(DB_FILE):
            self.data = copy.deepcopy(DEFAULT_DATA)
            self.save_data()
            return self.data

        try:
            with open(DB_FILE, "r", encoding="utf-8") as file:
                loaded = json.load(file)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"File dữ liệu {DB_FILE} không phải JSON hợp lệ. "
                "Hãy khôi phục bản sao lưu hoặc sửa file trước khi chạy."
            ) from exc

        if not isinstance(loaded, dict):
            raise RuntimeError(f"File dữ liệu {DB_FILE} phải chứa một JSON object.")

        data = copy.deepcopy(DEFAULT_DATA)
        data.update(loaded)
        data["coords"] = {**DEFAULT_DATA["coords"], **loaded.get("coords", {})}
        data["accounts"] = self._normalize_accounts(loaded.get("accounts"))
        data["urls"] = self._normalize_urls(loaded.get("urls", DEFAULT_URLS))
        data["code_pool"] = self._normalize_code_pool(loaded)
        data["all_codes"] = list(data["code_pool"])

        last_account = loaded.get("last_account")
        data["last_account"] = (
            last_account if last_account in data["accounts"] else next(iter(data["accounts"]))
        )
        self.data = data
        self.save_data()
        return data

    @staticmethod
    def _normalize_accounts(accounts):
        if not isinstance(accounts, dict) or not accounts:
            return copy.deepcopy(DEFAULT_DATA["accounts"])

        normalized = {}
        for name, account in accounts.items():
            if not isinstance(name, str) or not isinstance(account, dict):
                continue
            used_codes = account.get("used_codes", [])
            if not isinstance(used_codes, list):
                used_codes = []
            normalized[name] = {
                **account,
                "used_codes": list(
                    dict.fromkeys(
                        code.strip().upper()
                        for code in used_codes
                        if isinstance(code, str) and code.strip()
                    )
                ),
            }
        return normalized or copy.deepcopy(DEFAULT_DATA["accounts"])

    @staticmethod
    def _normalize_urls(urls):
        if not isinstance(urls, list):
            return list(DEFAULT_URLS)
        return list(dict.fromkeys(url.strip() for url in urls if isinstance(url, str) and url.strip()))

    @staticmethod
    def _normalize_code_pool(loaded):
        raw_pool = loaded.get("code_pool", {})
        pool = {}
        if isinstance(raw_pool, dict):
            for code, info in raw_pool.items():
                if not isinstance(code, str) or not code.strip():
                    continue
                clean_code = code.strip().upper()
                if isinstance(info, dict):
                    status = info.get("status", "new")
                    if status not in {"new", "valid", "dead"}:
                        status = "new"
                    sources = info.get("sources", [])
                    results = info.get("account_results", {})
                    pool[clean_code] = {
                        "status": status,
                        "sources": list(
                            dict.fromkeys(
                                source.strip()
                                for source in sources
                                if isinstance(source, str) and source.strip()
                            )
                        )
                        if isinstance(sources, list)
                        else [],
                        "account_results": results if isinstance(results, dict) else {},
                    }
                else:
                    pool[clean_code] = {
                        "status": "new",
                        "sources": [],
                        "account_results": {},
                    }

        legacy_codes = loaded.get("all_codes", [])
        if isinstance(legacy_codes, list):
            for code in legacy_codes:
                if isinstance(code, str) and code.strip():
                    clean_code = code.strip().upper()
                    info = pool.setdefault(
                        clean_code,
                        {"status": "new", "sources": [], "account_results": {}},
                    )
                    if "Kho cũ" not in info["sources"]:
                        info["sources"].append("Kho cũ")

        accounts = loaded.get("accounts", {})
        if isinstance(accounts, dict):
            for account in accounts.values():
                if not isinstance(account, dict):
                    continue
                used_codes = account.get("used_codes", [])
                if not isinstance(used_codes, list):
                    continue
                for code in used_codes:
                    if isinstance(code, str) and code.strip():
                        clean_code = code.strip().upper()
                        info = pool.setdefault(
                            clean_code,
                            {"status": "new", "sources": [], "account_results": {}},
                        )
                        if "Lịch sử cũ" not in info["sources"]:
                            info["sources"].append("Lịch sử cũ")
        return pool

    def save_data(self, data=None):
        if data is not None:
            self.data = data
        with open(DB_FILE, "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)

    @staticmethod
    def validate_url(url):
        parsed = urlparse(url.strip())
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and not parsed.username
            and not parsed.password
        )

    def get_urls(self):
        return list(self.data["urls"])

    def save_urls(self, url_list):
        urls = list(dict.fromkeys(url.strip() for url in url_list if url.strip()))
        invalid_urls = [url for url in urls if not self.validate_url(url)]
        if invalid_urls:
            raise ValueError(f"URL không hợp lệ (chỉ chấp nhận HTTP/HTTPS): {invalid_urls[0]}")
        self.data["urls"] = urls
        self.save_data()

    # --- Quản lý tọa độ và cấu hình ---
    def save_coord(self, key, pos_tuple, color_tuple=None):
        self.data["coords"][key] = list(pos_tuple)
        if color_tuple is not None:
            self.data["coords"]["modal_color"] = list(color_tuple)
        self.save_data()

    def get_coords(self):
        return self.data["coords"]

    def save_delay(self, delay_val):
        self.data["delay"] = delay_val
        self.save_data()

    # --- Quản lý tài khoản ---
    def get_account_names(self):
        return list(self.data["accounts"])

    def add_account(self, name):
        name = name.strip()
        if not name or name in self.data["accounts"]:
            return False
        self.data["accounts"][name] = {"used_codes": []}
        self.data["last_account"] = name
        self.save_data()
        return True

    def delete_account(self, name):
        if len(self.data["accounts"]) <= 1 or name not in self.data["accounts"]:
            return False
        del self.data["accounts"][name]
        self.data["last_account"] = next(iter(self.data["accounts"]))
        for info in self.data["code_pool"].values():
            info.get("account_results", {}).pop(name, None)
            if info.get("status") == "valid" and not any(
                result == "success"
                for result in info.get("account_results", {}).values()
            ):
                info["status"] = "new"
        self.save_data()
        return True

    def set_last_account(self, name):
        if name in self.data["accounts"]:
            self.data["last_account"] = name
            self.save_data()

    # --- Quản lý kho code, nguồn và kết quả ---
    def add_codes_to_pool(self, raw_codes, source="Nhập tay"):
        added_count = 0
        for code in raw_codes:
            if not isinstance(code, str):
                continue
            clean_code = code.strip().upper()
            if not clean_code:
                continue
            if clean_code not in self.data["code_pool"]:
                self.data["code_pool"][clean_code] = {
                    "status": "new",
                    "sources": [source],
                    "account_results": {},
                }
                added_count += 1
            else:
                sources = self.data["code_pool"][clean_code].setdefault("sources", [])
                if source not in sources:
                    sources.append(source)

        self.data["all_codes"] = list(self.data["code_pool"])
        if raw_codes:
            self.save_data()
        return added_count

    def add_codes_with_sources(self, code_sources):
        new_count = 0
        existing_count = 0
        for code, sources in code_sources.items():
            if not isinstance(code, str):
                continue
            clean_code = code.strip().upper()
            if not clean_code:
                continue
            source_list = list(dict.fromkeys(sources))
            if clean_code not in self.data["code_pool"]:
                self.data["code_pool"][clean_code] = {
                    "status": "new",
                    "sources": source_list,
                    "account_results": {},
                }
                new_count += 1
            else:
                existing_count += 1
                existing_sources = self.data["code_pool"][clean_code].setdefault("sources", [])
                existing_sources.extend(
                    source for source in source_list if source not in existing_sources
                )

        self.data["all_codes"] = list(self.data["code_pool"])
        if code_sources:
            self.save_data()
        return new_count, existing_count

    def get_pending_codes_for_account(self, account_name):
        if account_name not in self.data["accounts"]:
            return []
        used = set(self.data["accounts"][account_name]["used_codes"])
        return [
            code
            for code, info in self.data["code_pool"].items()
            if code not in used and info.get("status") != "dead"
        ]

    def set_code_status(self, code, status):
        if status not in {"new", "valid", "dead"}:
            raise ValueError(f"Trạng thái code không hợp lệ: {status}")
        clean_code = code.strip().upper()
        if clean_code not in self.data["code_pool"]:
            raise KeyError(f"Không tìm thấy code trong kho: {clean_code}")
        self.data["code_pool"][clean_code]["status"] = status
        self.save_data()

    def update_code_result(self, account_name, code, is_success):
        clean_code = code.strip().upper()
        if not clean_code:
            return
        info = self.data["code_pool"].setdefault(
            clean_code,
            {"status": "new", "sources": ["Nhập tay"], "account_results": {}},
        )
        if account_name in self.data["accounts"]:
            used_codes = self.data["accounts"][account_name]["used_codes"]
            if clean_code not in used_codes:
                used_codes.append(clean_code)
            info.setdefault("account_results", {})[account_name] = (
                "success" if is_success else "failed"
            )

        if is_success:
            info["status"] = "valid"
        elif info.get("status") != "valid":
            info["status"] = "new"

        self.data["all_codes"] = list(self.data["code_pool"])
        self.save_data()

    def mark_code_processed(self, account_name, code):
        self.update_code_result(account_name, code, is_success=False)

    def reset_account_history(self, account_name):
        if account_name not in self.data["accounts"]:
            return
        self.data["accounts"][account_name]["used_codes"] = []
        for info in self.data["code_pool"].values():
            results = info.setdefault("account_results", {})
            results.pop(account_name, None)
            if info.get("status") == "valid" and not any(
                result == "success" for result in results.values()
            ):
                info["status"] = "new"
        self.save_data()
