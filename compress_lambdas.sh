#!/bin/bash

SOURCE_DIR="./lifewatch_batch_platform/backend_lamdas"
TARGET_DIR="./lifewatch_batch_platform/backend_lambda_artifacts"

mkdir -p "$TARGET_DIR"

echo "Zipping python files..."

zip -j "$TARGET_DIR/logs_lambda.zip" "$SOURCE_DIR/logs.py"
zip -j "$TARGET_DIR/results_lambda.zip" "$SOURCE_DIR/results.py"
zip -j "$TARGET_DIR/status_lambda.zip" "$SOURCE_DIR/status.py"
zip -j "$TARGET_DIR/lambda.zip" "$SOURCE_DIR/lambda_function.py"

echo "Lambdas compressed to $TARGET_DIR."