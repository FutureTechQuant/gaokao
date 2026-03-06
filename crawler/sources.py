SOURCES = [
    {
        "name": "阳光高考",
        "url": "https://gaokao.chsi.com.cn/",
        "must_include": [
            "高考", "普通高考", "志愿", "录取", "招生", "报名", "查分", "分数线", "考试"
        ],
        "exclude_keywords": [
            "考研", "研究生", "博士", "硕士", "自考", "成考", "四六级", "留学"
        ],
        "allow_domains": [
            "gaokao.chsi.com.cn", "www.chsi.com.cn", "chsi.com.cn"
        ]
    },
    {
        "name": "示例-某省教育考试院",
        "url": "https://example.gov.cn/gaokao/list.html",
        "must_include": [
            "高考", "普通高考", "志愿填报", "录取", "分数线", "报名", "查分"
        ],
        "exclude_keywords": [
            "研究生", "自考", "成考", "教师资格"
        ],
        "allow_domains": [
            "example.gov.cn"
        ]
    }
]
