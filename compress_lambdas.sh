#!/bin/bash

BACKEND_LAMBDAS_DIR="./lifewatch_batch_platform/backend_lambdas"
ARTIFACTS_DIR="./lifewatch_batch_platform/backend_lambda_artifacts"

mkdir -p "$ARTIFACTS_DIR"

for lambda_dir in "$BACKEND_LAMBDAS_DIR"/*; do
    if [ -d "$lambda_dir" ]; then
        lambda_name=$(basename "$lambda_dir")
        output_file="$ARTIFACTS_DIR/${lambda_name}.zip"
        
        echo "Compressing $lambda_name..."
        cd "$lambda_dir"
        zip -r "../../$output_file" .
        cd - > /dev/null
        
        echo "✓ Created $output_file"
    fi
done

echo "All lambdas compressed successfully!"