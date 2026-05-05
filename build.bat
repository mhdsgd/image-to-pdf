@echo off
REM build.bat - Windows打包脚本

echo 开始打包...

REM 安装依赖
pip install -r requirements.txt

REM 打包应用程序
pyinstaller build/build.spec

echo 打包完成！
echo 可执行文件位于: dist/图片合并PDF工具.exe

pause
