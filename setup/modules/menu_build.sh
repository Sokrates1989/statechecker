#!/bin/bash
#
# menu_build.sh
#
# Build operations module for Statechecker quick-start menu.
# This module provides functions for building Docker images for Statechecker.
#
# Author: Auto-generated
# Date: 2026-01-29
# Version: 1.0.0

MENU_BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

read_prompt() {
    # Read a prompt from stdin (works in interactive and non-interactive shells).
    #
    # Args:
    #   $1: prompt text
    #   $2: variable name
    local prompt="$1"
    local var_name="$2"

    if [[ -r /dev/tty ]]; then
        read -r -p "$prompt" "$var_name" < /dev/tty
    else
        read -r -p "$prompt" "$var_name"
    fi
}

handle_build_image() {
    # Build the production image (if build-image script exists).
    echo "🏗️  Building production Docker image..."
    echo ""
    if [ -f "build-image/build-image.sh" ]; then
        bash build-image/build-image.sh
    else
        echo "❌ build-image/build-image.sh not found"
    fi
}

handle_build_web_image() {
    # Build the nginx-based admin website Docker image (Dockerfile_web).
    echo "🏗️  Building website Docker image (nginx)..."
    echo ""

    if [ ! -f "Dockerfile_web" ]; then
        echo "❌ Dockerfile_web not found"
        return 1
    fi

    local image_name="sokrates1989/statechecker-web"
    local image_version="latest"

    if [ -f .env ]; then
        image_name=$(grep "^WEB_IMAGE_NAME=" .env 2>/dev/null | cut -d'=' -f2- | tr -d ' "' || echo "$image_name")
        image_version=$(grep "^WEB_IMAGE_VERSION=" .env 2>/dev/null | cut -d'=' -f2- | tr -d ' "' || echo "$image_version")
    fi

    read_prompt "Website image name [$image_name]: " input_name
    if [ -n "$input_name" ]; then
        image_name="$input_name"
    fi

    read_prompt "Website image version [$image_version]: " input_version
    if [ -n "$input_version" ]; then
        image_version="$input_version"
    fi
    if [ -z "$image_version" ]; then
        image_version="latest"
    fi

    local full_image="${image_name}:${image_version}"
    local target_platform="${TARGET_PLATFORM:-linux/amd64}"

    echo "" 
    echo "📦 Building: $full_image"
    echo "Target platform: $target_platform"

    if docker buildx version >/dev/null 2>&1; then
        docker buildx build --platform "$target_platform" -t "$full_image" -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$image_version" --load .
    else
        docker build -t "$full_image" -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$image_version" .
    fi

    echo "📤 Pushing image to registry..."
    docker push "$full_image"
    echo "✅ Image pushed: $full_image"

    if [ "$image_version" != "latest" ]; then
        echo ""
        echo "📤 Tagging and pushing ${image_name}:latest..."
        docker tag "$full_image" "${image_name}:latest"
        docker push "${image_name}:latest"
        echo "✅ Also pushed: ${image_name}:latest"
    fi

    if [ -f .env ]; then
        if grep -q '^WEB_IMAGE_NAME=' .env; then
            tmp_env="$(mktemp)" || return 1
            sed "s|^WEB_IMAGE_NAME=.*|WEB_IMAGE_NAME=$image_name|" .env > "$tmp_env" && mv "$tmp_env" .env
        else
            echo "WEB_IMAGE_NAME=$image_name" >> .env
        fi
        if grep -q '^WEB_IMAGE_VERSION=' .env; then
            tmp_env="$(mktemp)" || return 1
            sed "s|^WEB_IMAGE_VERSION=.*|WEB_IMAGE_VERSION=$image_version|" .env > "$tmp_env" && mv "$tmp_env" .env
        else
            echo "WEB_IMAGE_VERSION=$image_version" >> .env
        fi
    fi
}
