#!/bin/bash

echo "======================================================="
echo "    Pornire Sistem de Analiza a Continutului"
echo "======================================================="
echo ""

if [ ! -f ".env" ]; then
    echo "Fisierul de setari (.env) nu exista. Sa il configuram!"
    cp .env.example .env
    
    echo ""
    read -p "Te rugam sa introduci cheia ta secreta Gemini API: " GEMINI_KEY
    
    sed -i "s/GEMINI_API_KEY=/GEMINI_API_KEY=${GEMINI_KEY}/" .env
    
    echo ""
    echo "Cheia a fost salvata cu succes!"
    echo "======================================================="
fi

echo ""
echo "Pornim platforma in fundal prin Docker..."
echo "Te rugam sa astepti, prima lansare dureaza putin pentru a instala totul!"
echo ""

docker-compose up --build -d

echo ""
echo "======================================================="
echo "Aplicatia a pornit cu succes si ruleaza!"
echo ""
echo "Acces:"
echo "- Interfata web: http://localhost:8080"
echo "- Backend API:   http://localhost:8000"
echo "======================================================="
echo ""
