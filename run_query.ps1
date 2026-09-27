param(
    [string]$Query = "What is the steel pipe design formula in ASME B31.8, and what do the variables represent?"
)

$env:PYTHONUTF8 = "1"
Write-Host "Querying ASME B31.8 RAG Agent with: '$Query'" -ForegroundColor Cyan
& .venv\Scripts\nat.exe run --config_file asme_rag_config.yml --input $Query
