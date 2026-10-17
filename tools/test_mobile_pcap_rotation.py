#!/usr/bin/env python3
"""Exercise production mobile PCAP rotation against real files and I/O failures."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main/vendor/pcap.c").read_text(encoding="utf-8")
START = SOURCE.index("static esp_err_t pcap_rotate_mobile_segment(FILE **stream) {")
END = SOURCE.index("\n/* Hands the buffer", START)
ROTATE = SOURCE[START:END]

HARNESS = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define CONFIG_HELTEC_ANDROID_STORAGE 1
#define ANDROID_SPOOL_SEGMENT_BYTES (128U * 1024U)
#define MAX_FILE_NAME_LENGTH 512
#define PCAP_TAG "PCAP"
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_LOGE(...) ((void)0)
typedef int esp_err_t;
static char pcap_file_path[MAX_FILE_NAME_LENGTH];
static const char *pcap_dir_path;
static char pcap_base_name[32];
static int s_capture_type;
static size_t buffer_offset = 4;
static unsigned session;
static unsigned next_segment;
static int fail_open;
static int fail_header;
static int fail_close;
static int fail_flush;

static FILE *rotation_fopen(const char *path, const char *mode) {
  if (fail_open > 0) { --fail_open; return NULL; }
  FILE *stream = fopen(path, mode);
  // POSIX permits ab+ to start reads at zero (glibc) or EOF (Darwin).
  // Force the zero-position case on every host so recovery is deterministic.
  if (stream && strcmp(mode, "ab+") == 0) assert(fseek(stream, 0, SEEK_SET) == 0);
  return stream;
}
static int rotation_fclose(FILE *stream) {
  const int result = fclose(stream);
  if (fail_close) { fail_close = 0; return EOF; }
  return result;
}
static int rotation_fflush(FILE *stream) {
  if (fail_flush) { fail_flush = 0; return EOF; }
  return fflush(stream);
}
static void get_next_pcap_file_name(char *path, const char *dir, const char *base) {
  snprintf(path, MAX_FILE_NAME_LENGTH, "%s/%s_%u.pcap", dir, base, next_segment++);
}
static esp_err_t pcap_write_global_header(FILE *stream, int type) {
  (void)type;
  if (fail_header) { fail_header = 0; return ESP_FAIL; }
  const uint8_t header[24] = {0xd4, 0xc3, 0xb2, 0xa1};
  return fwrite(header, 1, sizeof(header), stream) == sizeof(header) ? ESP_OK : ESP_FAIL;
}
#define fopen rotation_fopen
#define fclose rotation_fclose
#define fflush rotation_fflush
'''

CASES = r'''
#undef fopen
#undef fclose
#undef fflush

static FILE *prepare(size_t size) {
  snprintf(pcap_base_name, sizeof(pcap_base_name), "capture%u", session++);
  next_segment = 0;
  get_next_pcap_file_name(pcap_file_path, pcap_dir_path, pcap_base_name);
  FILE *stream = fopen(pcap_file_path, "wb+");
  assert(stream);
  if (size) {
    assert(fseek(stream, size - 1, SEEK_SET) == 0);
    assert(fputc(0x5a, stream) != EOF);
  }
  assert(fflush(stream) == 0);
  return stream;
}
static size_t length(const char *path) {
  struct stat info;
  assert(stat(path, &info) == 0);
  return (size_t)info.st_size;
}
int main(int argc, char **argv) {
  assert(argc == 2);
  pcap_dir_path = argv[1];
  char previous[MAX_FILE_NAME_LENGTH];
  FILE *stream = prepare(0);
  strcpy(previous, pcap_file_path);
  assert(pcap_rotate_mobile_segment(&stream) == ESP_OK);
  assert(strcmp(previous, pcap_file_path) == 0);
  assert(fclose(stream) == 0);

  stream = prepare(ANDROID_SPOOL_SEGMENT_BYTES - buffer_offset);
  strcpy(previous, pcap_file_path);
  assert(pcap_rotate_mobile_segment(&stream) == ESP_OK);
  assert(strcmp(previous, pcap_file_path) == 0);
  assert(fclose(stream) == 0);

  stream = prepare(ANDROID_SPOOL_SEGMENT_BYTES - 1);
  strcpy(previous, pcap_file_path);
  assert(pcap_rotate_mobile_segment(&stream) == ESP_OK);
  assert(strcmp(previous, pcap_file_path) != 0);
  assert(length(previous) == ANDROID_SPOOL_SEGMENT_BYTES - 1);
  assert(ftell(stream) == 24);
  assert(fclose(stream) == 0);

  stream = prepare(ANDROID_SPOOL_SEGMENT_BYTES);
  strcpy(previous, pcap_file_path);
  fail_open = 1;
  assert(pcap_rotate_mobile_segment(&stream) == ESP_FAIL);
  assert(stream && strcmp(previous, pcap_file_path) == 0);
  assert(length(previous) == ANDROID_SPOOL_SEGMENT_BYTES);
  assert(pcap_rotate_mobile_segment(&stream) == ESP_OK);
  assert(strcmp(previous, pcap_file_path) != 0);
  assert(fclose(stream) == 0);

  stream = prepare(ANDROID_SPOOL_SEGMENT_BYTES);
  strcpy(previous, pcap_file_path);
  fail_header = 1;
  assert(pcap_rotate_mobile_segment(&stream) == ESP_FAIL);
  assert(stream && strcmp(previous, pcap_file_path) == 0);
  assert(length(previous) == ANDROID_SPOOL_SEGMENT_BYTES);
  char failed_segment[MAX_FILE_NAME_LENGTH];
  snprintf(failed_segment, sizeof(failed_segment), "%s/%s_1.pcap", pcap_dir_path, pcap_base_name);
  assert(access(failed_segment, F_OK) != 0);
  assert(fclose(stream) == 0);

  stream = prepare(ANDROID_SPOOL_SEGMENT_BYTES);
  strcpy(previous, pcap_file_path);
  fail_open = 2;
  assert(pcap_rotate_mobile_segment(&stream) == ESP_FAIL);
  assert(stream == NULL && strcmp(previous, pcap_file_path) == 0);
  assert(length(previous) == ANDROID_SPOOL_SEGMENT_BYTES);
  stream = fopen(pcap_file_path, "ab+");
  assert(stream && pcap_rotate_mobile_segment(&stream) == ESP_OK);
  assert(fclose(stream) == 0);

  stream = prepare(ANDROID_SPOOL_SEGMENT_BYTES);
  strcpy(previous, pcap_file_path);
  fail_close = 1;
  assert(pcap_rotate_mobile_segment(&stream) == ESP_FAIL);
  assert(stream && strcmp(previous, pcap_file_path) == 0);
  assert(fclose(stream) == 0);

  stream = prepare(ANDROID_SPOOL_SEGMENT_BYTES);
  strcpy(previous, pcap_file_path);
  fail_flush = 1;
  assert(pcap_rotate_mobile_segment(&stream) == ESP_FAIL);
  assert(stream && strcmp(previous, pcap_file_path) == 0);
  assert(pcap_rotate_mobile_segment(&stream) == ESP_OK);
  assert(fclose(stream) == 0);
  puts("Mobile PCAP rotation: 8 boundary and I/O-failure cases passed");
  return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="ghost-mobile-pcap-") as temporary:
    work = Path(temporary)
    source = work / "rotation.c"
    binary = work / "rotation-test"
    source.write_text(HARNESS + ROTATE + CASES, encoding="utf-8")
    subprocess.run(
        ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary), str(work)], check=True)
