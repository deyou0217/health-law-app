# 卫健法律法规检索系统

一款面向卫生健康系统工作人员的法律法规检索工具，支持14个权威来源并发搜索。

## 功能特性

- **14源并发搜索**：国家卫健委、各省市卫健委、疾控中心官网、微信公众号全覆盖
- **权威来源优先**：政府网站（site:gov.cn）优先展示
- **智能去重**：Jaccard相似度算法对搜索结果去重
- **离线可用**：PyInstaller打包，下载exe直接运行，无需安装Python
- **内置法规**：内置常用卫生健康法律法规

## 下载使用

前往 [Releases](https://github.com/deyou0217/health-law-app/releases) 页面下载 `HealthLawSearch_v1.0.exe`，双击运行即可（Windows 64位）。

## 搜索来源

| 来源 | 说明 |
|------|------|
| 国家卫健委 | 权威法律法规、政策文件 |
| 各省市卫健委 | 覆盖全国31省市（site:gov.cn站内搜索） |
| 疾控中心 | 国家及地方疾控中心官网 |
| 微信公众号 | 搜狗微信搜索，覆盖卫健领域公众号 |

## 技术栈

- Python 3.12 + Tkinter（GUI）
- requests + BeautifulSoup（网页抓取）
- ThreadPoolExecutor（并发搜索）
- PyInstaller（打包exe）

## 源码结构

| 文件 | 说明 |
|------|------|
| main.py | 主程序入口，GUI界面 |
| searcher.py | 搜索引擎核心，14源并发 |
| build_app.py | PyInstaller打包脚本 |
| builtin_laws.py | 内置法律法规数据 |
| doc_generator.py | 文档生成工具 |

## License

MIT
