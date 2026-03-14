$SourceDir = ".\lifewatch_batch_platform\backend_lamdas"
$TargetDir = ".\lifewatch_batch_platform\backend_lambda_artifacts"

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

Write-Host "Zipping python files..."

Compress-Archive -Path "$SourceDir\logs.py" -DestinationPath "$TargetDir\logs_lambda.zip" -Force
Compress-Archive -Path "$SourceDir\results.py" -DestinationPath "$TargetDir\results_lambda.zip" -Force
Compress-Archive -Path "$SourceDir\status.py" -DestinationPath "$TargetDir\status_lambda.zip" -Force
Compress-Archive -Path "$SourceDir\lambda_function.py" -DestinationPath "$TargetDir\lambda.zip" -Force

Write-Host "Lambdas compressed to $TargetDir."