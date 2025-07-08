#!/bin/bash

# Function to build, tag and push images for releases via nix
build_and_push_release() {
  local nix_target="$1"
  local source_tag="$2"
  local target_image="$3"
  local tag_prefix="$4"
  local version="$5"
  local arch_suffix="$6"
  local system="$7"

  local final_tag="${tag_prefix}${version}-${arch_suffix}"

  echo "Building and pushing $source_tag -> $target_image:$final_tag"
  nix run .#"${nix_target}".copyToDockerDaemon --system "${system}"
  docker tag "${source_tag}":latest "${target_image}":"${final_tag}"
  docker push "${target_image}":"${final_tag}"
}

# Function to create and push multi-arch manifest for releases via nix
create_release_manifest() {
  local image="$1"
  local tag="$2"
  local tag_prefix="$3"
  local version="$4"

  local amd64_tag="${tag_prefix}${version}-amd64"
  local arm64_tag="${tag_prefix}${version}-arm64"

  echo "Creating manifest for $image:$tag"
  docker manifest create "${image}":"${tag}" \
    --amend "${image}":"${amd64_tag}" \
    --amend "${image}":"${arm64_tag}"
  docker manifest push "${image}":"${tag}"
}

# Export functions for use in CI
export -f build_and_push_release
export -f create_release_manifest
