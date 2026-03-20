$SourceDir = ".\lifewatch_batch_platform\terraform\backend_lambdas"
$TargetDir = ".\lifewatch_batch_platform\terraform\backend_lambda_artifacts"

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

Write-Host "Zipping python files with shared dependencies..."

Compress-Archive -Path "$SourceDir\logs.py", "$SourceDir\handle_cors.py" -DestinationPath "$TargetDir\logs_lambda.zip" -Force
Compress-Archive -Path "$SourceDir\results.py", "$SourceDir\handle_cors.py" -DestinationPath "$TargetDir\results_lambda.zip" -Force
Compress-Archive -Path "$SourceDir\status.py", "$SourceDir\handle_cors.py" -DestinationPath "$TargetDir\status_lambda.zip" -Force
Compress-Archive -Path "$SourceDir\lambda_function.py", "$SourceDir\handle_cors.py" -DestinationPath "$TargetDir\lambda.zip" -Force
Compress-Archive -Path "$SourceDir\history_list.py", "$SourceDir\handle_cors.py" -DestinationPath "$TargetDir\history_list_lambda.zip" -Force

Write-Host "Lambdas compressed to $TargetDir."
