import assert from "node:assert/strict";
import test from "node:test";
import { zstdCompressSync } from "node:zlib";

import { dumpMrs, parseDecompressedMrs } from "../scripts/dump_mrs.mjs";


function u64(value) {
  const buffer = Buffer.alloc(8);
  buffer.writeBigUInt64BE(BigInt(value));
  return buffer;
}


function header(behavior, count) {
  return Buffer.concat([Buffer.from("MRS\x01", "binary"), Buffer.from([behavior]), u64(count), u64(0)]);
}


function ipv6(value) {
  const groups = value.split(":");
  const empty = groups.indexOf("");
  let expanded = groups;
  if (empty >= 0) {
    const left = groups.slice(0, empty).filter(Boolean);
    const right = groups.slice(empty + 1).filter(Boolean);
    expanded = [...left, ...Array(8 - left.length - right.length).fill("0"), ...right];
  }
  const buffer = Buffer.alloc(16);
  expanded.forEach((group, index) => buffer.writeUInt16BE(Number.parseInt(group || "0", 16), index * 2));
  return buffer;
}


test("decodes an IPv6 MRS range into its canonical prefix", () => {
  const payload = Buffer.concat([
    header(1, 1),
    Buffer.from([1]),
    u64(1),
    ipv6("2402:f000::"),
    ipv6("2402:f000:ffff:ffff:ffff:ffff:ffff:ffff"),
  ]);
  assert.deepEqual(parseDecompressedMrs(payload, "ipcidr"), ["2402:f000::/32"]);
  assert.deepEqual(dumpMrs(zstdCompressSync(payload), "ipcidr"), ["2402:f000::/32"]);
});


test("decodes a one-key domain MRS trie", () => {
  const reversed = Buffer.from("moc.elgoog.www");
  const nodeCount = reversed.length + 1;
  let leaves = 1n << BigInt(reversed.length);
  let bitmap = 0n;
  for (let node = 0; node < reversed.length; node += 1) bitmap |= 1n << BigInt(node * 2 + 1);
  bitmap |= 1n << BigInt(reversed.length * 2);

  const payload = Buffer.concat([
    header(0, 1),
    Buffer.from([1]),
    u64(1),
    u64(leaves),
    u64(1),
    u64(bitmap),
    u64(reversed.length),
    reversed,
  ]);
  assert.equal(nodeCount, 15);
  assert.deepEqual(parseDecompressedMrs(payload, "domain"), ["www.google.com"]);
});


test("reverses decoded domain keys by Unicode code point", () => {
  const domain = "例子.测试";
  const reversed = Buffer.from(Array.from(domain).reverse().join(""));
  let leaves = 1n << BigInt(reversed.length);
  let bitmap = 0n;
  for (let node = 0; node < reversed.length; node += 1) bitmap |= 1n << BigInt(node * 2 + 1);
  bitmap |= 1n << BigInt(reversed.length * 2);

  const payload = Buffer.concat([
    header(0, 1),
    Buffer.from([1]),
    u64(1),
    u64(leaves),
    u64(1),
    u64(bitmap),
    u64(reversed.length),
    reversed,
  ]);
  assert.deepEqual(parseDecompressedMrs(payload, "domain"), [domain]);
});
