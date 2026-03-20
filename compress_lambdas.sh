#!/bin/bash

SOURCE_DIR="./lifewatch_batch_platform/terraform/backend_lambdas"
TARGET_DIR="./lifewatch_batch_platform/terraform/backend_lambda_artifacts"

mkdir -p "$TARGET_DIR"

echo "Zipping python files with shared dependencies..."

zip -j "$TARGET_DIR/logs_lambda.zip" \
    "$SOURCE_DIR/logs.py" \
    "$SOURCE_DIR/handle_cors.py"

zip -j "$TARGET_DIR/results_lambda.zip" \
    "$SOURCE_DIR/results.py" \
    "$SOURCE_DIR/handle_cors.py"

zip -j "$TARGET_DIR/status_lambda.zip" \
    "$SOURCE_DIR/status.py" \
    "$SOURCE_DIR/handle_cors.py"

zip -j "$TARGET_DIR/lambda.zip" \
    "$SOURCE_DIR/lambda_function.py" \
    "$SOURCE_DIR/handle_cors.py"

zip -j "$TARGET_DIR/history_list_lambda.zip" \
    "$SOURCE_DIR/history_list.py" \
    "$SOURCE_DIR/handle_cors.py"

echo "Lambdas compressed to $TARGET_DIR."
