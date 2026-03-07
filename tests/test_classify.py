from crawler.classify.category import assign_category
from crawler.classify.topic import assign_topic


def test_assign_category():
    item = {"title": "2024届毕业生就业质量年度报告", "snippet": "", "topic": "careers"}
    assert assign_category(item) == "就业质量"


def test_assign_topic():
    item = {"title": "2025年推免生接收办法", "snippet": ""}
    assert assign_topic(item) == "保研信息"
