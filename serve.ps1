# Launch ASME B31.8 RAG Agent REST API Server
$env:PYTHONUTF8 = "1"
Write-Host "Starting ASME B31.8 RAG API Server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Write-Host "Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
& .venv\Scripts\nat.exe serve --config_file asme_rag_config.yml --host 127.0.0.1 --port 8000
