SOURCES = [
    # ================= 全国性政策 =================
    {
        "name": "教育部-普通高校招生公告",
        "url": "http://www.moe.gov.cn/srcsite/A15/moe_776/s3258/",
        "must_include": [
            "招生", "高考", "录取", "强基计划", "普通高校"
        ],
        "exclude_keywords": [
            "考研", "研究生", "成人", "自考"
        ],
        "allow_domains": ["moe.gov.cn"]
    },

    # ================= 陕西省官方招考平台 =================
    {
        "name": "陕西省教育考试院-普通高考",
        "url": "http://www.sneea.cn/xwzx/ptgk.htm",
        "must_include": [
            "高考", "招生", "录取", "志愿", "报名", "分数线", "查分", "统考", "成绩"
        ],
        "exclude_keywords": [
            "研究生", "硕士", "自考", "成考", "专升本", "教师资格"
        ],
        "allow_domains": ["sneea.cn", "www.sneea.cn"]
    },
    {
        "name": "陕西招生考试信息网-高考资讯",
        "url": "https://www.sneac.com/ptgk.htm",
        "must_include": [
            "高考", "招生", "录取", "志愿", "报名", "分数线", "查分", "成绩"
        ],
        "exclude_keywords": [
            "研究生", "自考", "成考", "专升本", "社会考试"
        ],
        "allow_domains": ["sneac.com", "www.sneac.com"]
    },

    # ================= 陕西省重点高校本科招生网 =================
    {
        "name": "西安交通大学-本科招生通知公告",
        "url": "http://zs.xjtu.edu.cn/tzgg.htm",
        "must_include": [
            "招生", "高考", "强基计划", "少年班", "录取", "简章", "专项计划"
        ],
        "exclude_keywords": [
            "研究生", "硕士", "博士", "招聘", "采购"
        ],
        "allow_domains": ["zs.xjtu.edu.cn", "xjtu.edu.cn"]
    },
    {
        "name": "西北工业大学-本科招生公告",
        "url": "https://zsb.nwpu.edu.cn/tzgg.htm",
        "must_include": [
            "招生", "高考", "强基计划", "录取", "分数线", "简章"
        ],
        "exclude_keywords": [
            "研究生", "硕士", "博士"
        ],
        "allow_domains": ["zsb.nwpu.edu.cn", "nwpu.edu.cn"]
    },
    {
        "name": "西安电子科技大学-本科招生公告",
        "url": "https://zsb.xidian.edu.cn/tzgg.htm",
        "must_include": [
            "招生", "高考", "录取", "分数线", "政策", "简章"
        ],
        "exclude_keywords": [
            "研究生", "硕士", "博士"
        ],
        "allow_domains": ["zsb.xidian.edu.cn", "xidian.edu.cn"]
    },
    {
        "name": "西北农林科技大学-本科招生公告",
        "url": "https://zhshw.nwafu.edu.cn/tzgg/index.htm",
        "must_include": [
            "招生", "高考", "录取", "分数线", "简章"
        ],
        "exclude_keywords": [
            "研究生", "硕士", "博士"
        ],
        "allow_domains": ["zhshw.nwafu.edu.cn", "nwafu.edu.cn"]
    },
    {
        "name": "陕西师范大学-本科招生公告",
        "url": "http://zsb.snnu.edu.cn/tzgg.htm",
        "must_include": [
            "招生", "高考", "公费师范生", "优师计划", "录取", "简章"
        ],
        "exclude_keywords": [
            "研究生", "硕士", "博士", "成考"
        ],
        "allow_domains": ["zsb.snnu.edu.cn", "snnu.edu.cn"]
    },
    {
        "name": "西北大学-本科招生公告",
        "url": "https://zsb.nwu.edu.cn/tzgg.htm",
        "must_include": [
            "招生", "高考", "录取", "分数线", "简章"
        ],
        "exclude_keywords": [
            "研究生", "硕士", "博士"
        ],
        "allow_domains": ["zsb.nwu.edu.cn", "nwu.edu.cn"]
    }
]
