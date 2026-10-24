@echo off
cd frontend
if not exist node_modules call npm install
npm run dev
