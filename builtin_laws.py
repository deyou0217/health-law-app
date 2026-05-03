# -*- coding: utf-8 -*-
"""
预置法律法规数据库 - 卫健领域核心法律法规
支持离线检索，每条记录包含名称、文号、发布机关、发布日期、分类、来源链接
"""

BUILTIN_LAWS = [
    {
        "title": "中华人民共和国基本医疗卫生与健康促进法",
        "doc_number": "中华人民共和国主席令第三十八号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2019年12月28日",
        "effective_date": "2020年6月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2019-12/29/content_5464861.htm",
        "summary": "我国卫生健康领域第一部基础性、综合性法律，涵盖基本医疗卫生服务、医疗卫生机构、医疗卫生人员、药品供应保障、健康促进、资金保障等内容。"
    },
    {
        "title": "中华人民共和国传染病防治法",
        "doc_number": "中华人民共和国主席令第十七号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2013年6月29日",
        "effective_date": "2013年6月29日",
        "category": "法律",
        "source_url": "https://www.gov.cn/guoqing/2021-10/29/content_5647625.htm",
        "summary": "规定传染病预防、疫情报告通报和公布、疫情控制、医疗救治、监督管理、保障措施等内容，是传染病防控的核心法律。"
    },
    {
        "title": "中华人民共和国疫苗管理法",
        "doc_number": "中华人民共和国主席令第三十号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2019年6月29日",
        "effective_date": "2019年12月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2019-06/30/content_5404540.htm",
        "summary": "对疫苗研制、生产、流通、预防接种等全链条进行规范管理，建立疫苗追溯体系，规定异常反应补偿等制度。"
    },
    {
        "title": "中华人民共和国医师法",
        "doc_number": "中华人民共和国主席令第九十四号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2021年8月20日",
        "effective_date": "2022年3月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2021-08/20/content_5632423.htm",
        "summary": "规范医师执业行为，保障医师合法权益，涵盖考试注册、执业规则、培训和考核、保障措施等内容。"
    },
    {
        "title": "中华人民共和国药品管理法",
        "doc_number": "中华人民共和国主席令第三十一号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2019年8月26日",
        "effective_date": "2019年12月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2019-08/26/content_5424780.htm",
        "summary": "规范药品研制、生产、经营、使用、监督管理，建立药品追溯制度，强化药品安全责任。"
    },
    {
        "title": "中华人民共和国职业病防治法",
        "doc_number": "中华人民共和国主席令第二十四号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2018年12月29日",
        "effective_date": "2018年12月29日",
        "category": "法律",
        "source_url": "https://www.gov.cn/guoqing/2021-10/29/content_5647626.htm",
        "summary": "预防、控制和消除职业病危害，防治职业病，保护劳动者健康及其相关权益。"
    },
    {
        "title": "中华人民共和国母婴保健法",
        "doc_number": "中华人民共和国主席令第三十三号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2017年11月4日",
        "effective_date": "2017年11月5日",
        "category": "法律",
        "source_url": "https://www.gov.cn/guoqing/2021-10/29/content_5647627.htm",
        "summary": "保障母亲和婴儿健康，提高出生人口素质，涵盖婚前保健、孕产期保健、技术鉴定等内容。"
    },
    {
        "title": "中华人民共和国献血法",
        "doc_number": "中华人民共和国主席令第九十三号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "1997年12月29日",
        "effective_date": "1998年10月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/banshi/2005-05/26/content_969.htm",
        "summary": "保证医疗临床用血需要和安全，保障献血者和用血者身体健康，实行无偿献血制度。"
    },
    {
        "title": "中华人民共和国精神卫生法",
        "doc_number": "中华人民共和国主席令第六十二号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2018年4月27日",
        "effective_date": "2018年4月27日",
        "category": "法律",
        "source_url": "https://www.gov.cn/guoqing/2021-10/29/content_5647628.htm",
        "summary": "发展精神卫生事业，规范精神卫生服务，维护精神障碍患者的合法权益。"
    },
    {
        "title": "中华人民共和国中医药法",
        "doc_number": "中华人民共和国主席令第五十九号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2016年12月25日",
        "effective_date": "2017年7月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2016-12/26/content_5152773.htm",
        "summary": "继承和弘扬中医药，保障和促进中医药事业发展，涵盖中医药服务、中药保护与发展、人才培养等内容。"
    },
    {
        "title": "中华人民共和国食品安全法",
        "doc_number": "中华人民共和国主席令第二十一号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2018年12月29日",
        "effective_date": "2018年12月29日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2015-04/25/content_2852919.htm",
        "summary": "保证食品安全，保障公众身体健康和生命安全，涵盖食品安全风险监测评估、安全标准、生产经营、检验、进出口、事故处置、监督管理等内容。"
    },
    {
        "title": "中华人民共和国人口与计划生育法",
        "doc_number": "中华人民共和国主席令第九十六号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2021年8月20日",
        "effective_date": "2021年8月20日",
        "category": "法律",
        "source_url": "https://www.gov.cn/guoqing/2021-10/29/content_5647631.htm",
        "summary": "实现人口与经济、社会、资源、环境的协调发展，推行三孩政策，完善计划生育服务管理。"
    },
    {
        "title": "中华人民共和国红十字会法",
        "doc_number": "中华人民共和国主席令第六十三号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2017年2月24日",
        "effective_date": "2017年5月8日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2017-02/24/content_5170623.htm",
        "summary": "保护人的生命和健康，维护人的尊严，规范和保障红十字会履行职责。"
    },
    {
        "title": "中华人民共和国生物安全法",
        "doc_number": "中华人民共和国主席令第五十六号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2020年10月17日",
        "effective_date": "2021年4月15日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2020-10/18/content_5552225.htm",
        "summary": "维护国家生物安全，防范和应对生物安全风险，涵盖生物技术研究、实验室生物安全、人类遗传资源管理、传染病防控等。"
    },
    {
        "title": "中华人民共和国固体废物污染环境防治法",
        "doc_number": "中华人民共和国主席令第四十三号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2020年4月29日",
        "effective_date": "2020年9月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/xinwen/2020-04/30/content_5507561.htm",
        "summary": "防治固体废物污染环境，规范医疗废物分类收集、贮存、运输和处置等环节。"
    },
    {
        "title": "中华人民共和国突发事件应对法",
        "doc_number": "中华人民共和国主席令第六十九号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2024年6月28日",
        "effective_date": "2024年11月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/yaowen/liebiao/202411/content_6987003.htm",
        "summary": "预防和减少突发事件的发生，规范突发事件应对活动，保护人民生命财产安全。"
    },
    {
        "title": "中华人民共和国国境卫生检疫法",
        "doc_number": "中华人民共和国主席令第六号",
        "issuer": "全国人民代表大会常务委员会",
        "publish_date": "2024年6月28日",
        "effective_date": "2025年1月1日",
        "category": "法律",
        "source_url": "https://www.gov.cn/yaowen/liebiao/202407/content_6956556.htm",
        "summary": "防止传染病由国境传入传出，规范国境卫生检疫工作，保护人体健康和公共卫生安全。"
    },
    {
        "title": "医疗机构管理条例",
        "doc_number": "国务院令第149号",
        "issuer": "国务院",
        "publish_date": "2022年3月29日",
        "effective_date": "2022年5月1日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/zhengce/content/2022-03/30/content_5682197.htm",
        "summary": "规范医疗机构的设置审批、登记校验、执业管理、监督管理等内容。"
    },
    {
        "title": "护士条例",
        "doc_number": "国务院令第517号",
        "issuer": "国务院",
        "publish_date": "2020年3月27日",
        "effective_date": "2020年3月27日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/zhengce/2020-12/27/content_5574676.htm",
        "summary": "规范护士执业行为，保障护士合法权益，促进护理事业发展。"
    },
    {
        "title": "医疗纠纷预防和处理条例",
        "doc_number": "国务院令第701号",
        "issuer": "国务院",
        "publish_date": "2018年7月31日",
        "effective_date": "2018年10月1日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/zhengce/content/2018-08/09/content_5312716.htm",
        "summary": "预防和妥善处理医疗纠纷，保护医患双方合法权益，维护医疗秩序。"
    },
    {
        "title": "突发公共卫生事件应急条例",
        "doc_number": "国务院令第376号",
        "issuer": "国务院",
        "publish_date": "2011年1月8日",
        "effective_date": "2011年1月8日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/gongbao/content/2011/content_1860797.htm",
        "summary": "有效预防、及时控制和消除突发公共卫生事件的危害，保障公众身体健康与生命安全，维护正常的社会秩序。"
    },
    {
        "title": "中华人民共和国母婴保健法实施办法",
        "doc_number": "国务院令第308号",
        "issuer": "国务院",
        "publish_date": "2022年3月29日",
        "effective_date": "2022年5月1日",
        "category": "行政法规",
        "source_url": "https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3NTJiN2Q0YTAxNzVlNDc2NmJhYjA5Mjc",
        "summary": "实施母婴保健法的具体细则，规范婚前保健、孕产期保健、婴儿保健等服务。"
    },
    {
        "title": "艾滋病防治条例",
        "doc_number": "国务院令第457号",
        "issuer": "国务院",
        "publish_date": "2019年3月2日",
        "effective_date": "2019年3月2日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/zhengce/2020-12/27/content_5574683.htm",
        "summary": "预防和控制艾滋病的发生与流行，保障人体健康和公共卫生。"
    },
    {
        "title": "医疗机构病历管理规定",
        "doc_number": "国卫医发〔2013〕31号",
        "issuer": "国家卫生计生委（原）",
        "publish_date": "2013年12月17日",
        "effective_date": "2014年1月1日",
        "category": "部门规章",
        "source_url": "https://www.gov.cn/gongbao/content/2014/content_2634100.htm",
        "summary": "规范医疗机构病历管理，保障医疗质量和医疗安全，维护医患双方合法权益。"
    },
    {
        "title": "处方管理办法",
        "doc_number": "卫生部令第53号",
        "issuer": "卫生部（原）",
        "publish_date": "2007年2月14日",
        "effective_date": "2007年5月1日",
        "category": "部门规章",
        "source_url": "https://www.gov.cn/flfg/2007-03/13/content_549406.htm",
        "summary": "规范处方管理，提高处方质量，促进合理用药，保障医疗安全。"
    },
    {
        "title": "医院感染管理办法",
        "doc_number": "卫生部令第48号",
        "issuer": "卫生部（原）",
        "publish_date": "2006年9月1日",
        "effective_date": "2006年9月1日",
        "category": "部门规章",
        "source_url": "https://www.gov.cn/gongbao/content/2007/content_537905.htm",
        "summary": "加强医院感染管理，有效预防和控制医院感染，提高医疗质量，保证医疗安全。"
    },
    {
        "title": "医疗废物管理条例",
        "doc_number": "国务院令第380号",
        "issuer": "国务院",
        "publish_date": "2011年1月8日",
        "effective_date": "2011年1月8日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/zhengce/2020-12/27/content_5574674.htm",
        "summary": "加强医疗废物的安全管理，防止疾病传播，保护环境，保障人体健康。"
    },
    {
        "title": "公共场所卫生管理条例",
        "doc_number": "国务院令第714号",
        "issuer": "国务院",
        "publish_date": "2019年4月23日",
        "effective_date": "2019年4月23日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/gongbao/content/2019/content_5395464.htm",
        "summary": "创造良好的公共场所卫生条件，预防疾病，保障人体健康。"
    },
    {
        "title": "学校卫生工作条例",
        "doc_number": "国家教育委员会令第10号／卫生部令第1号",
        "issuer": "国家教委／卫生部",
        "publish_date": "1990年6月4日",
        "effective_date": "1990年6月4日",
        "category": "行政法规",
        "source_url": "https://www.gov.cn/gongbao/content/2011/content_1860798.htm",
        "summary": "加强学校卫生工作，提高学生健康水平，涵盖学校教学卫生、环境卫生、传染病防控等内容。"
    },
    {
        "title": "生活饮用水卫生监督管理办法",
        "doc_number": "建设部、卫生部令第53号",
        "issuer": "建设部／卫生部",
        "publish_date": "2016年4月17日",
        "effective_date": "2016年6月1日",
        "category": "部门规章",
        "source_url": "https://www.gov.cn/gongbao/content/2016/content_5114683.htm",
        "summary": "保证生活饮用水卫生安全，保障人体健康，规范饮用水卫生监督管理。"
    },
    {
        "title": "中华人民共和国基本医疗卫生与健康促进法" + "（典型案例·普法案例）",
        "doc_number": "指导性案例",
        "issuer": "最高人民法院",
        "publish_date": "2020年",
        "effective_date": "",
        "category": "典型案例",
        "source_url": "https://www.court.gov.cn/shenpan-gengduo-132.html",
        "summary": "最高人民法院发布的医疗卫生领域指导性案例，涉及医疗损害责任纠纷、医疗保险纠纷等。"
    },
]

def search_builtin(keyword: str, category: str = ""):
    """从预置数据库中搜索法律法规"""
    results = []
    keyword = keyword.strip().lower()
    for law in BUILTIN_LAWS:
        match = False
        if keyword in law["title"].lower() or keyword in law["summary"].lower():
            match = True
        if not match:
            for field in ["doc_number", "issuer"]:
                if keyword in law.get(field, "").lower():
                    match = True
                    break
        if category and law["category"] != category:
            match = False
        if match:
            results.append(law.copy())
    return results

def get_categories():
    """获取所有分类"""
    cats = set()
    for law in BUILTIN_LAWS:
        cats.add(law["category"])
    return sorted(cats)


if __name__ == "__main__":
    # 简单测试
    import json
    res = search_builtin("传染病")
    print(f"搜索'传染病'结果: {len(res)} 条")
    for r in res:
        print(f"  - [{r['category']}] {r['title']} ({r['doc_number']})")
    print(f"\n分类: {get_categories()}")
