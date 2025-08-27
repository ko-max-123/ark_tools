@echo off
REM Python Environment Launcher
set PYTHONPATH=D:\04_github_dev\ark_tools\embedded_python\Lib\site-packages
set PATH=D:\04_github_dev\ark_tools\embedded_python;D:\04_github_dev\ark_tools\embedded_python\Scripts;%PATH%

REM メインスクリプトを実行
"D:\04_github_dev\ark_tools\embedded_python\python.exe" "D:\04_github_dev\ark_tools\tag_analysis.py" %*
