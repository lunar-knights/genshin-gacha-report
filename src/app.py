import os
import re
from urllib.parse import urlparse
import urllib.request
import json

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
QUERY_URL = "https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog"
MAX_PAGE_SIZE = 20
gacha_type2code = {
    "character": "301",
    "weapon": "302",
    "normal": "200",
    "novice": "100"
}
gt_eng2gt_chs = {
    "character": "人物祈愿",
    "weapon": "武器祈愿",
    "normal": "常驻祈愿",
    "novice": "新手祈愿"
}


class Runner(object):
    def __init__(self) -> None:
        super().__init__()
        self.USERPROFILE = os.environ["USERPROFILE"]
        self.genshin_log_path = os.path.join(
            self.USERPROFILE, "AppData", "LocalLow", "miHoYo", "原神", "output_log.txt")
        if not os.path.isfile(self.genshin_log_path):
            self.genshin_log_path = os.path.join(
                self.USERPROFILE, "AppData", "LocalLow", "miHoYo", "Genshin Impact", "output_log.txt")
        if not os.path.isfile(self.genshin_log_path):
            print("日志：%s不存在，无法获取记录，请运行游戏并在游戏中查看一次祈愿记录" % self.genshin_log_path)
        self.gacha_query_info = {}
        self.gacha_info = {}
        self.count_gacha_info = {}

    def get_temp_url(self):
        try:
            with open(self.genshin_log_path) as f:
                text = f.read()
            res = re.search(r"OnGetWebViewPageFinish:(.*#/log)", text)
            self.url = res.group(1)
        except:
            print("日志信息不全，无法获取记录，请运行游戏并在游戏中查看一次祈愿记录")

    def parse_temp_url(self):
        urldict = urlparse(self.url)
        query_text = urldict.query
        items = [i.split("=") for i in query_text.split("&")]
        for item in items:
            self.gacha_query_info[item[0]] = item[1]

    def get_gacha_info(self):
        print("当前每页数据量：%s条" % MAX_PAGE_SIZE)
        for gacha_type in gacha_type2code:
            self.gacha_info[gacha_type] = []
            curr_page = 1
            res = {"data": {"list": [""]}}
            while len(res["data"]["list"]) != 0:
                print("获取【%s】池，第%s页数据" % (gt_eng2gt_chs[gacha_type], curr_page))
                url = self._gen_query_url(gacha_type, curr_page)
                rep = urllib.request.urlopen(url)
                res = json.loads(rep.read().decode("UTF-8"))
                self.gacha_info[gacha_type].extend(res["data"]["list"])
                curr_page += 1

    def _gen_query_url(self, gacha_type, page):
        temp_gacha_info = self.gacha_query_info.copy()
        temp_gacha_info["gacha_type"] = gacha_type2code[gacha_type]
        temp_gacha_info["page"] = page
        temp_gacha_info["size"] = MAX_PAGE_SIZE
        q_list = []
        for k in temp_gacha_info:
            q_list.append("%s=%s" % (k, temp_gacha_info[k]))
        q_str = "&".join(q_list)
        query_url = QUERY_URL + "?" + q_str
        return query_url

    def analyse_gacha_info(self):
        all_total = 0
        all_count = {"3": 0, "4": 0, "5": 0}
        for gacha_type in self.gacha_info:
            gacha_result = self.gacha_info[gacha_type]
            count = {"3": 0, "4": 0, "5": 0}
            total = 0
            for item in gacha_result:
                total += 1
                all_total += 1
                count[item["rank_type"]] += 1
                all_count[item["rank_type"]] += 1
            self.count_gacha_info[gacha_type] = {}
            self.count_gacha_info[gacha_type]["total"] = total
            self.count_gacha_info[gacha_type]["count"] = count
        self.count_gacha_info["all"] = {}
        self.count_gacha_info["all"]["total"] = all_total
        self.count_gacha_info["all"]["count"] = all_count

    def gen_report(self):
        report = os.path.join(CURR_PATH, "report.txt")
        with open(report, "w", encoding="UTF-8") as f:
            for gacha_type in self.count_gacha_info:
                count = self.count_gacha_info[gacha_type]["count"]
                total = self.count_gacha_info[gacha_type]["total"]
                if gacha_type != "all":
                    res_str = "【%s】池中，总共祈愿%s次\n获取5星%s个，占比%.4f\n获取4星%s个，占比%.4f\n获取3星%s个，占比%.4f\n" % \
                        (gt_eng2gt_chs[gacha_type], total,
                         count["5"], count["5"] / total,
                         count["4"], count["4"] / total,
                         count["3"], count["3"] / total)
                else:
                    res_str = "总计祈愿%s次\n获取5星%s个，占比%.4f\n获取4星%s个，占比%.4f\n获取3星%s个，占比%.4f\n" % \
                        (total,
                         count["5"], count["5"] / total,
                         count["4"], count["4"] / total,
                         count["3"], count["3"] / total)
                print(res_str)
                f.write(res_str + "\n")

    def run(self):
        try:
            self.get_temp_url()
            self.parse_temp_url()
            self.get_gacha_info()
            self.analyse_gacha_info()
            self.gen_report()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    r = Runner()
    r.run()
    input("input anything to exit...")
