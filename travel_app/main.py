"""
travel_app 程序入口
运行命令：
    python main.py
"""
from __future__ import annotations

import sys
import traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from app import __version__
from app.main_window import MainWindow

# 高德地图HTML，内嵌JS地图API
MAP_HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>高德地图</title>
<style>html,body,#container{width:100%;height:100%;margin:0;padding:0;}</style>
<script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key=78825e4e5219b80a9fe44df433e35771"></script>
</head>
<body>
<div id="container"></div>
<script>
var map = new AMap.Map("container", {
    zoom:12,
    center:[112.9388,28.2282]  //长沙经纬度
});
// 添加标记点
new AMap.Marker({position:[112.9388,28.2282]}).setMap(map);
</script>
</body>
</html>
'''

def main() -> int:
    # 高分屏自适应
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # 初始化应用
    app = QApplication(sys.argv)
    app.setApplicationName("Travel Assistant")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("TravelApp Team")  # 新增机构名，用于本地配置存储

    # 创建并展示主窗口
    main_win = MainWindow()
    main_win.show()

    # 启动事件循环，返回退出码
    return app.exec_()


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as e:
        # 全局捕获启动异常，打印完整堆栈
        print("程序启动发生未知错误：")
        traceback.print_exc()
        exit_code = 1

    raise SystemExit(exit_code)