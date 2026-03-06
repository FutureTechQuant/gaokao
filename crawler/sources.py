SOURCES = [
    {
        "name": "阳光高考",
        "url": "https://gaokao.chsi.com.cn/",
        "must_include": [
            "高考", "志愿", "录取", "招生", "报名", "查分", "分数线", "考试"
        ],
        "exclude_keywords": [
            "考研", "就业", "留学", "四六级", "成人高考"
        ],
        "allow_domains": ["gaokao.chsi.com.cn", "www.chsi.com.cn", "chsi.com.cn"]
    },

    # ===== 把下面这些替换成你真实关注的官方列表页 =====
    {
        "name": "示例-某省教育考试院",
        "url": "https://example.gov.cn/gaokao/list.html",
        "must_include": [
            "高考", "普通高考", "志愿填报", "录取", "分数线", "报名", "查分"
        ],
        "exclude_keywords": [
            "研究生", "自考", "成考", "教师资格"
        ],
        "allow_domains": ["example.gov.cn"]
    },
    {
        "name": "示例-某大学本科招生网",
        "url": "https://zsb.example.edu.cn/news/",
        "must_include": [
            "本科招生", "高考", "录取", "招生章程", "报名", "志愿"
        ],
        "exclude_keywords": [
            "研究生", "博士", "硕士"
        ],
        "allow_domains": ["zsb.example.edu.cn", "example.edu.cn"]
    },
]
