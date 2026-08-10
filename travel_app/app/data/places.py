"""内置地名表，用于目的地输入自动匹配。

结构：
- 直辖市 / 特别行政区：仅显示地名本身（如「北京」「香港」）。
- 各省/自治区的地级市：显示「省份.城市」（如「湖南.长沙」）。
- 国外：仅显示所属国家（如「日本」），不细分城市。

国内条目整体排在国外之前，使 QCompleter 优先匹配国内城市。
places_for(lang) 返回当前语言下的显示字符串列表。
"""

from __future__ import annotations

from typing import List, Tuple

from app.i18n import LANG_EN, LANG_ZH

# 直辖市 / 特别行政区 —— 仅显示地名本身
MUNICIPALITIES: List[Tuple[str, str]] = [
    ("北京", "Beijing"),
    ("上海", "Shanghai"),
    ("天津", "Tianjin"),
    ("重庆", "Chongqing"),
    ("香港", "Hong Kong"),
    ("澳门", "Macao"),
]

# 各省/自治区的地级市：(省中, Province EN, [(市中, City EN), ...])
PROVINCES: List[Tuple[str, str, List[Tuple[str, str]]]] = [
    ("河北", "Hebei", [
        ("石家庄", "Shijiazhuang"), ("唐山", "Tangshan"), ("秦皇岛", "Qinhuangdao"),
        ("邯郸", "Handan"), ("保定", "Baoding"), ("张家口", "Zhangjiakou"),
        ("承德", "Chengde"), ("沧州", "Cangzhou"), ("廊坊", "Langfang"),
    ]),
    ("山西", "Shanxi", [
        ("太原", "Taiyuan"), ("大同", "Datong"), ("阳泉", "Yangquan"),
        ("长治", "Changzhi"), ("晋城", "Jincheng"), ("晋中", "Jinzhong"),
        ("运城", "Yuncheng"), ("临汾", "Linfen"),
    ]),
    ("辽宁", "Liaoning", [
        ("沈阳", "Shenyang"), ("大连", "Dalian"), ("鞍山", "Anshan"),
        ("抚顺", "Fushun"), ("本溪", "Benxi"), ("丹东", "Dandong"),
        ("锦州", "Jinzhou"), ("营口", "Yingkou"), ("盘锦", "Panjin"),
        ("朝阳", "Chaoyang"), ("葫芦岛", "Huludao"),
    ]),
    ("吉林", "Jilin", [
        ("长春", "Changchun"), ("吉林", "Jilin"), ("四平", "Siping"),
        ("辽源", "Liaoyuan"), ("通化", "Tonghua"), ("白山", "Baishan"),
        ("松原", "Songyuan"), ("白城", "Baicheng"), ("延边", "Yanbian"),
    ]),
    ("黑龙江", "Heilongjiang", [
        ("哈尔滨", "Harbin"), ("齐齐哈尔", "Qiqihar"), ("鸡西", "Jixi"),
        ("大庆", "Daqing"), ("佳木斯", "Jiamusi"), ("牡丹江", "Mudanjiang"),
        ("黑河", "Heihe"), ("绥化", "Suihua"), ("大兴安岭", "Daxinganling"),
    ]),
    ("江苏", "Jiangsu", [
        ("南京", "Nanjing"), ("无锡", "Wuxi"), ("徐州", "Xuzhou"),
        ("常州", "Changzhou"), ("苏州", "Suzhou"), ("南通", "Nantong"),
        ("连云港", "Lianyungang"), ("淮安", "Huai'an"), ("盐城", "Yancheng"),
        ("扬州", "Yangzhou"), ("镇江", "Zhenjiang"), ("泰州", "Taizhou"),
        ("宿迁", "Suqian"),
    ]),
    ("浙江", "Zhejiang", [
        ("杭州", "Hangzhou"), ("宁波", "Ningbo"), ("温州", "Wenzhou"),
        ("嘉兴", "Jiaxing"), ("湖州", "Huzhou"), ("绍兴", "Shaoxing"),
        ("金华", "Jinhua"), ("衢州", "Quzhou"), ("舟山", "Zhoushan"),
        ("台州", "Taizhou"), ("丽水", "Lishui"),
    ]),
    ("安徽", "Anhui", [
        ("合肥", "Hefei"), ("芜湖", "Wuhu"), ("蚌埠", "Bengbu"),
        ("淮南", "Huainan"), ("马鞍山", "Ma'anshan"), ("淮北", "Huaibei"),
        ("铜陵", "Tongling"), ("安庆", "Anqing"), ("黄山", "Huangshan"),
        ("滁州", "Chuzhou"), ("阜阳", "Fuyang"), ("宿州", "Suzhou"),
        ("六安", "Lu'an"), ("亳州", "Bozhou"), ("池州", "Chizhou"),
        ("宣城", "Xuancheng"),
    ]),
    ("福建", "Fujian", [
        ("福州", "Fuzhou"), ("厦门", "Xiamen"), ("莆田", "Putian"),
        ("三明", "Sanming"), ("泉州", "Quanzhou"), ("漳州", "Zhangzhou"),
        ("南平", "Nanping"), ("龙岩", "Longyan"), ("宁德", "Ningde"),
    ]),
    ("江西", "Jiangxi", [
        ("南昌", "Nanchang"), ("景德镇", "Jingdezhen"), ("萍乡", "Pingxiang"),
        ("九江", "Jiujiang"), ("新余", "Xinyu"), ("鹰潭", "Yingtan"),
        ("赣州", "Ganzhou"), ("吉安", "Ji'an"), ("宜春", "Yichun"),
        ("抚州", "Fuzhou"), ("上饶", "Shangrao"),
    ]),
    ("山东", "Shandong", [
        ("济南", "Jinan"), ("青岛", "Qingdao"), ("淄博", "Zibo"),
        ("枣庄", "Zaozhuang"), ("东营", "Dongying"), ("烟台", "Yantai"),
        ("潍坊", "Weifang"), ("济宁", "Jining"), ("泰安", "Tai'an"),
        ("威海", "Weihai"), ("日照", "Rizhao"), ("临沂", "Linyi"),
        ("德州", "Dezhou"), ("聊城", "Liaocheng"), ("滨州", "Binzhou"),
        ("菏泽", "Heze"),
    ]),
    ("河南", "Henan", [
        ("郑州", "Zhengzhou"), ("开封", "Kaifeng"), ("洛阳", "Luoyang"),
        ("平顶山", "Pingdingshan"), ("安阳", "Anyang"), ("新乡", "Xinxiang"),
        ("焦作", "Jiaozuo"), ("许昌", "Xuchang"), ("漯河", "Luohe"),
        ("南阳", "Nanyang"), ("商丘", "Shangqiu"), ("信阳", "Xinyang"),
        ("周口", "Zhoukou"), ("驻马店", "Zhumadian"),
    ]),
    ("湖北", "Hubei", [
        ("武汉", "Wuhan"), ("黄石", "Huangshi"), ("十堰", "Shiyan"),
        ("宜昌", "Yichang"), ("襄阳", "Xiangyang"), ("鄂州", "Ezhou"),
        ("荆门", "Jingmen"), ("孝感", "Xiaogan"), ("荆州", "Jingzhou"),
        ("黄冈", "Huanggang"), ("咸宁", "Xianning"), ("随州", "Suizhou"),
        ("恩施", "Enshi"),
    ]),
    ("湖南", "Hunan", [
        ("长沙", "Changsha"), ("株洲", "Zhuzhou"), ("湘潭", "Xiangtan"),
        ("衡阳", "Hengyang"), ("邵阳", "Shaoyang"), ("岳阳", "Yueyang"),
        ("常德", "Changde"), ("张家界", "Zhangjiajie"), ("益阳", "Yiyang"),
        ("郴州", "Chenzhou"), ("永州", "Yongzhou"), ("怀化", "Huaihua"),
        ("娄底", "Loudi"), ("湘西", "Xiangxi"),
    ]),
    ("广东", "Guangdong", [
        ("广州", "Guangzhou"), ("深圳", "Shenzhen"), ("珠海", "Zhuhai"),
        ("汕头", "Shantou"), ("佛山", "Foshan"), ("韶关", "Shaoguan"),
        ("湛江", "Zhanjiang"), ("肇庆", "Zhaoqing"), ("江门", "Jiangmen"),
        ("茂名", "Maoming"), ("惠州", "Huizhou"), ("梅州", "Meizhou"),
        ("汕尾", "Shanwei"), ("阳江", "Yangjiang"), ("清远", "Qingyuan"),
        ("东莞", "Dongguan"), ("中山", "Zhongshan"), ("潮州", "Chaozhou"),
        ("揭阳", "Jieyang"), ("云浮", "Yunfu"),
    ]),
    ("海南", "Hainan", [
        ("海口", "Haikou"), ("三亚", "Sanya"), ("三沙", "Sansha"),
        ("儋州", "Danzhou"),
    ]),
    ("四川", "Sichuan", [
        ("成都", "Chengdu"), ("自贡", "Zigong"), ("攀枝花", "Panzhihua"),
        ("泸州", "Luzhou"), ("德阳", "Deyang"), ("绵阳", "Mianyang"),
        ("广元", "Guangyuan"), ("遂宁", "Suining"), ("内江", "Neijiang"),
        ("乐山", "Leshan"), ("南充", "Nanchong"), ("眉山", "Meishan"),
        ("宜宾", "Yibin"), ("广安", "Guang'an"), ("达州", "Dazhou"),
        ("雅安", "Ya'an"), ("巴中", "Bazhong"), ("资阳", "Ziyang"),
        ("阿坝", "Aba"), ("甘孜", "Garze"), ("凉山", "Liangshan"),
    ]),
    ("贵州", "Guizhou", [
        ("贵阳", "Guiyang"), ("六盘水", "Liupanshui"), ("遵义", "Zunyi"),
        ("安顺", "Anshun"), ("毕节", "Bijie"), ("铜仁", "Tongren"),
        ("黔东南", "Qiandongnan"), ("黔南", "Qiannan"), ("黔西南", "Qianxinan"),
    ]),
    ("云南", "Yunnan", [
        ("昆明", "Kunming"), ("曲靖", "Qujing"), ("玉溪", "Yuxi"),
        ("保山", "Baoshan"), ("昭通", "Zhaotong"), ("丽江", "Lijiang"),
        ("普洱", "Pu'er"), ("临沧", "Lincang"), ("楚雄", "Chuxiong"),
        ("红河", "Honghe"), ("文山", "Wenshan"), ("西双版纳", "Xishuangbanna"),
        ("大理", "Dali"), ("德宏", "Dehong"), ("迪庆", "Diqing"),
    ]),
    ("陕西", "Shaanxi", [
        ("西安", "Xi'an"), ("铜川", "Tongchuan"), ("宝鸡", "Baoji"),
        ("咸阳", "Xianyang"), ("渭南", "Weinan"), ("延安", "Yan'an"),
        ("汉中", "Hanzhong"), ("榆林", "Yulin"), ("安康", "Ankang"),
        ("商洛", "Shangluo"),
    ]),
    ("甘肃", "Gansu", [
        ("兰州", "Lanzhou"), ("嘉峪关", "Jiayuguan"), ("金昌", "Jinchang"),
        ("白银", "Baiyin"), ("天水", "Tianshui"), ("武威", "Wuwei"),
        ("张掖", "Zhangye"), ("平凉", "Pingliang"), ("酒泉", "Jiuquan"),
        ("庆阳", "Qingyang"), ("定西", "Dingxi"), ("陇南", "Longnan"),
    ]),
    ("青海", "Qinghai", [
        ("西宁", "Xining"), ("海东", "Haidong"), ("海北", "Haibei"),
        ("黄南", "Huangnan"), ("果洛", "Guoluo"), ("玉树", "Yushu"),
        ("海西", "Haixi"),
    ]),
    ("台湾", "Taiwan", [
        ("台北", "Taipei"), ("新北", "New Taipei"), ("桃园", "Taoyuan"),
        ("台中", "Taichung"), ("台南", "Tainan"), ("高雄", "Kaohsiung"),
    ]),
    ("内蒙古", "Inner Mongolia", [
        ("呼和浩特", "Hohhot"), ("包头", "Baotou"), ("乌海", "Wuhai"),
        ("赤峰", "Chifeng"), ("通辽", "Tongliao"), ("鄂尔多斯", "Ordos"),
        ("呼伦贝尔", "Hulunbuir"), ("巴彦淖尔", "Bayannur"), ("乌兰察布", "Ulanqab"),
    ]),
    ("广西", "Guangxi", [
        ("南宁", "Nanning"), ("柳州", "Liuzhou"), ("桂林", "Guilin"),
        ("梧州", "Wuzhou"), ("北海", "Beihai"), ("防城港", "Fangchenggang"),
        ("钦州", "Qinzhou"), ("贵港", "Guigang"), ("玉林", "Yulin"),
        ("百色", "Baise"), ("贺州", "Hezhou"), ("河池", "Hechi"),
        ("来宾", "Laibin"), ("崇左", "Chongzuo"),
    ]),
    ("西藏", "Tibet", [
        ("拉萨", "Lhasa"), ("日喀则", "Shigatse"), ("昌都", "Qamdo"),
        ("林芝", "Nyingchi"), ("山南", "Shannan"), ("那曲", "Nagqu"),
        ("阿里", "Ngari"),
    ]),
    ("宁夏", "Ningxia", [
        ("银川", "Yinchuan"), ("石嘴山", "Shizuishan"), ("吴忠", "Wuzhong"),
        ("固原", "Guyuan"), ("中卫", "Zhongwei"),
    ]),
    ("新疆", "Xinjiang", [
        ("乌鲁木齐", "Urumqi"), ("克拉玛依", "Karamay"), ("吐鲁番", "Turpan"),
        ("哈密", "Hami"), ("阿克苏", "Aksu"), ("喀什", "Kashgar"),
        ("和田", "Hotan"), ("伊犁", "Ili"), ("塔城", "Tacheng"),
        ("阿勒泰", "Altay"), ("昌吉", "Changji"), ("石河子", "Shihezi"),
    ]),
]

# 国外 —— 仅显示所属国家
FOREIGN: List[Tuple[str, str]] = [
    ("日本", "Japan"), ("韩国", "South Korea"), ("朝鲜", "North Korea"),
    ("蒙古", "Mongolia"), ("越南", "Vietnam"), ("老挝", "Laos"),
    ("柬埔寨", "Cambodia"), ("缅甸", "Myanmar"), ("泰国", "Thailand"),
    ("马来西亚", "Malaysia"), ("新加坡", "Singapore"), ("印度尼西亚", "Indonesia"),
    ("菲律宾", "Philippines"), ("文莱", "Brunei"), ("东帝汶", "East Timor"),
    ("印度", "India"), ("尼泊尔", "Nepal"), ("不丹", "Bhutan"),
    ("孟加拉国", "Bangladesh"), ("斯里兰卡", "Sri Lanka"), ("马尔代夫", "Maldives"),
    ("巴基斯坦", "Pakistan"), ("哈萨克斯坦", "Kazakhstan"), ("乌兹别克斯坦", "Uzbekistan"),
    ("阿联酋", "UAE"), ("沙特阿拉伯", "Saudi Arabia"), ("土耳其", "Turkey"),
    ("以色列", "Israel"), ("伊朗", "Iran"), ("伊拉克", "Iraq"),
    ("英国", "United Kingdom"), ("法国", "France"), ("德国", "Germany"),
    ("意大利", "Italy"), ("西班牙", "Spain"), ("葡萄牙", "Portugal"),
    ("荷兰", "Netherlands"), ("比利时", "Belgium"), ("瑞士", "Switzerland"),
    ("奥地利", "Austria"), ("瑞典", "Sweden"), ("挪威", "Norway"),
    ("芬兰", "Finland"), ("丹麦", "Denmark"), ("冰岛", "Iceland"),
    ("爱尔兰", "Ireland"), ("希腊", "Greece"), ("波兰", "Poland"),
    ("捷克", "Czechia"), ("匈牙利", "Hungary"), ("俄罗斯", "Russia"),
    ("乌克兰", "Ukraine"), ("美国", "United States"), ("加拿大", "Canada"),
    ("墨西哥", "Mexico"), ("巴西", "Brazil"), ("阿根廷", "Argentina"),
    ("智利", "Chile"), ("秘鲁", "Peru"), ("古巴", "Cuba"),
    ("澳大利亚", "Australia"), ("新西兰", "New Zealand"), ("埃及", "Egypt"),
    ("南非", "South Africa"), ("摩洛哥", "Morocco"), ("肯尼亚", "Kenya"),
    ("埃塞俄比亚", "Ethiopia"), ("尼日利亚", "Nigeria"),
]


def places_for(lang: str) -> List[str]:
    """返回指定语言下的地名显示字符串列表（国内在前，国外在后）。"""
    result: List[str] = []
    # 直辖市 / 特别行政区：仅地名本身
    for zh, en in MUNICIPALITIES:
        result.append(en if lang == LANG_EN else zh)
    # 各省地级市：省份.城市
    for prov_zh, prov_en, cities in PROVINCES:
        for city_zh, city_en in cities:
            if lang == LANG_EN:
                result.append(f"{prov_en}.{city_en}")
            else:
                result.append(f"{prov_zh}.{city_zh}")
    # 国外：仅国家
    for zh, en in FOREIGN:
        result.append(en if lang == LANG_EN else zh)
    return result
