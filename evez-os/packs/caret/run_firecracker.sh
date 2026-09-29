#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
PACK="$ROOT/packs/caret"

FIRECRACKER_BIN="${FIRECRACKER_BIN:-firecracker}"
API_SOCK="${API_SOCK:-/tmp/evez-caret-firecracker.sock}"
KERNEL_IMAGE="${KERNEL_IMAGE:-$PACK/vmlinux.bin}"
ROOTFS_IMAGE="${ROOTFS_IMAGE:-$PACK/rootfs.ext4}"
INPUT="${CARET_INPUT:-$PACK/fixtures/demo_geometry.json}"
OUTPUT="${CARET_OUTPUT:-$PACK/caret_result.json}"
MEMORY_MB="${MEMORY_MB:-256}"
VCPUS="${VCPUS:-1}"
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $0 [--dry-run]

Environment:
  FIRECRACKER_BIN  Firecracker executable
  API_SOCK         Firecracker API Unix socket
  KERNEL_IMAGE     Guest kernel image
  ROOTFS_IMAGE     Guest rootfs ext4 image
  CARET_INPUT      Input JSON
  CARET_OUTPUT     Expected guest result path
  MEMORY_MB        Guest memory, default 256
  VCPUS            Guest vCPUs, default 1
EOF
}

case "${1:-}" in
  --dry-run) DRY_RUN=1 ;;
  -h|--help) usage; exit 0 ;;
esac

if [ "$DRY_RUN" -eq 1 ]; then
  cat <<EOF
FIRECRACKER DRY RUN
binary=$FIRECRACKER_BIN
api_socket=$API_SOCK
kernel=$KERNEL_IMAGE
rootfs=$ROOTFS_IMAGE
vcpus=$VCPUS
memory_mb=$MEMORY_MB
input=$INPUT
guest_output=/opt/caret/result.json
guest_command=/usr/bin/python3 /opt/caret/caret_lap_interpreter.py /opt/caret/input.json --output /opt/caret/result.json
host_projection=$OUTPUT
EOF
  exit 0
fi

command -v "$FIRECRACKER_BIN" >/dev/null 2>&1 || {
  echo "ERROR: Firecracker binary not found: $FIRECRACKER_BIN" >&2
  exit 2
}
[ -e /dev/kvm ] || {
  echo "ERROR: /dev/kvm unavailable; refusing simulated VM execution" >&2
  exit 3
}
[ -f "$KERNEL_IMAGE" ] || {
  echo "ERROR: kernel image missing: $KERNEL_IMAGE" >&2
  exit 4
}
[ -f "$ROOTFS_IMAGE" ] || {
  echo "ERROR: rootfs image missing: $ROOTFS_IMAGE" >&2
  exit 5
}
[ -f "$INPUT" ] || {
  echo "ERROR: input JSON missing: $INPUT" >&2
  exit 6
}

rm -f "$API_SOCK"

"$FIRECRACKER_BIN" --api-sock "$API_SOCK" >/tmp/evez-caret-firecracker.log 2>&1 &
FC_PID=$!
trap 'kill "$FC_PID" 2>/dev/null || true; rm -f "$API_SOCK"' EXIT

for _ in $(seq 1 100); do
  [ -S "$API_SOCK" ] && break
  sleep 0.05
done
[ -S "$API_SOCK" ] || {
  echo "ERROR: Firecracker API socket did not appear" >&2
  cat /tmp/evez-caret-firecracker.log >&2 || true
  exit 7
}

put() {
  curl --silent --show-error --fail --unix-socket "$API_SOCK" \
    -X PUT -H 'Content-Type: application/json' "$1" -d "$2" >/dev/null
}

put /boot-source "$(cat <<JSON
{"kernel_image_path":"$KERNEL_IMAGE","boot_args":"console=ttyS0 reboot=k panic=1 pci=off"}
JSON
)"

put /drives/rootfs "$(cat <<JSON
{"drive_id":"rootfs","path_on_host":"$ROOTFS_IMAGE","is_root_device":true,"is_read_only":false}
JSON
)"

put /machine-config "$(cat <<JSON
{"vcpu_count":$VCPUS,"mem_size_mib":$MEMORY_MB,"smt":false,"track_dirty_pages":false}
JSON
)"

put /actions '{"action_type":"InstanceStart"}'

echo "Firecracker VM started."
echo "Guest result must be projected from /opt/caret/result.json by the guest image's init/service."
echo "Host spine projection is deliberately not fabricated by this launcher."
