@echo off
chcp 65001 > nul
echo ========================================================
echo   Отправка проекта "ФОРМА / 01" на GitHub Pages
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Обновление ветки gh-pages из dist...
git branch -D gh-pages >nul 2>&1
git subtree split --prefix dist -b gh-pages

echo [2/3] Отправка основной ветки (main)...
git push -u origin main

echo [3/3] Отправка ветки сайта (gh-pages)...
git push -u origin gh-pages

echo.
echo ========================================================
echo   Готово! Проверьте вкладку Settings -> Pages на GitHub.
echo ========================================================
pause
