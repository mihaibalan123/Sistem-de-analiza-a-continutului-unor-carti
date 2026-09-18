@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo     Pornire Sistem de Analiza a Continutului
echo =======================================================
echo.

if not exist ".env" (
    echo Fisierul de setari ^(.env^) nu exista. Sa il configuram!
    copy .env.example .env > nul
    
    echo.
    set /p GEMINI_KEY="Te rugam sa introduci cheia ta secreta Gemini API: "
    
    (for /F "tokens=1* delims=:" %%a in ('findstr /n "^" .env') do (
        set "line=%%b"
        if "!line!"=="GEMINI_API_KEY=" (
            echo GEMINI_API_KEY=!GEMINI_KEY!
        ) else (
            echo(!line!
        )
    )) > .env.tmp
    move /Y .env.tmp .env > nul
    
    echo.
    echo Cheia a fost salvata cu succes!
    echo =======================================================
)

echo.
echo Pornim platforma in fundal prin Docker...
echo Te rugam sa astepti, prima lansare dureaza putin pentru a instala totul!
echo.

docker-compose up --build -d

echo.
echo =======================================================
echo Aplicatia a pornit cu succes si ruleaza!
echo.
echo Acces:
echo - Interfata web: http://localhost:8080
echo - Backend API:   http://localhost:8000
echo =======================================================
echo.
pause
