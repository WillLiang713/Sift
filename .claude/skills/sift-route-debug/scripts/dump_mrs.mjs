#!/usr/bin/env node

import fs from "node:fs";
import { fileURLToPath } from "node:url";
import * as zlib from "node:zlib";


class Reader {
  constructor(buffer) {
    this.buffer = buffer;
    this.offset = 0;
  }

  bytes(length) {
    if (!Number.isSafeInteger(length) || length < 0 || this.offset + length > this.buffer.length) {
      throw new Error("invalid or truncated MRS length");
    }
    const value = this.buffer.subarray(this.offset, this.offset + length);
    this.offset += length;
    return value;
  }

  u8() {
    return this.bytes(1)[0];
  }

  u64() {
    const value = this.buffer.readBigUInt64BE(this.offset);
    this.offset += 8;
    if (value > BigInt(Number.MAX_SAFE_INTEGER)) {
      throw new Error("MRS length exceeds JavaScript safe integer range");
    }
    return Number(value);
  }
}


function readU64Array(reader) {
  const length = reader.u64();
  if (length < 1) {
    throw new Error("invalid empty MRS array");
  }
  const values = [];
  for (let index = 0; index < length; index += 1) {
    values.push(reader.buffer.readBigUInt64BE(reader.offset));
    reader.offset += 8;
  }
  return values;
}


function getBit(bitmap, index) {
  return Number((bitmap[index >> 6] >> BigInt(index & 63)) & 1n);
}


function dumpDomains(reader) {
  if (reader.u8() !== 1) {
    throw new Error("unsupported MRS domain-set version");
  }
  const leaves = readU64Array(reader);
  const labelBitmap = readU64Array(reader);
  const labels = reader.bytes(reader.u64());

  const logicalBits = labelBitmap.length * 64;
  const onesBefore = new Uint32Array(logicalBits + 1);
  const onePositions = [];
  for (let index = 0; index < logicalBits; index += 1) {
    const bit = getBit(labelBitmap, index);
    onesBefore[index + 1] = onesBefore[index] + bit;
    if (bit) onePositions.push(index);
  }
  const countZeros = (index) => index - onesBefore[index];
  const selectOne = (index) => {
    if (index < 0 || index >= onePositions.length) {
      throw new Error("invalid MRS domain bitmap");
    }
    return onePositions[index];
  };

  const keys = [];
  const current = [];
  const traverse = (nodeId, bitmapIndex) => {
    if (getBit(leaves, nodeId)) {
      const reversedDomain = Buffer.from(current).toString("utf8");
      keys.push(Array.from(reversedDomain).reverse().join(""));
    }
    for (let index = bitmapIndex; index < logicalBits; index += 1) {
      if (getBit(labelBitmap, index)) return;
      const labelIndex = index - nodeId;
      if (labelIndex < 0 || labelIndex >= labels.length) {
        throw new Error("invalid MRS domain label index");
      }
      current.push(labels[labelIndex]);
      const nextNodeId = countZeros(index + 1);
      const nextBitmapIndex = selectOne(nextNodeId - 1) + 1;
      traverse(nextNodeId, nextBitmapIndex);
      current.pop();
    }
    throw new Error("unterminated MRS domain bitmap");
  };
  traverse(0, 0);

  keys.sort();
  const keySet = new Set(keys);
  return keys.filter((key) => !keySet.has(`+.${key}`));
}


function bytesToBigInt(bytes) {
  let value = 0n;
  for (const byte of bytes) value = (value << 8n) | BigInt(byte);
  return value;
}


function isMappedIPv4(value) {
  return (value >> 32n) === 0xffffn;
}


function trailingZeros(value, bits) {
  if (value === 0n) return bits;
  let count = 0;
  while ((value & 1n) === 0n) {
    value >>= 1n;
    count += 1;
  }
  return count;
}


function floorLog2(value) {
  return value.toString(2).length - 1;
}


function formatIPv4(value) {
  return [24n, 16n, 8n, 0n].map((shift) => Number((value >> shift) & 255n)).join(".");
}


function formatIPv6(value) {
  const groups = [];
  for (let shift = 112n; shift >= 0n; shift -= 16n) {
    groups.push(Number((value >> shift) & 0xffffn));
  }
  let bestStart = -1;
  let bestLength = 0;
  for (let index = 0; index < groups.length;) {
    if (groups[index] !== 0) {
      index += 1;
      continue;
    }
    let end = index;
    while (end < groups.length && groups[end] === 0) end += 1;
    if (end - index > bestLength && end - index >= 2) {
      bestStart = index;
      bestLength = end - index;
    }
    index = end;
  }
  if (bestStart < 0) return groups.map((group) => group.toString(16)).join(":");
  const left = groups.slice(0, bestStart).map((group) => group.toString(16)).join(":");
  const right = groups.slice(bestStart + bestLength).map((group) => group.toString(16)).join(":");
  if (!left && !right) return "::";
  if (!left) return `::${right}`;
  if (!right) return `${left}::`;
  return `${left}::${right}`;
}


function rangeToPrefixes(first, last, bits, formatter) {
  const prefixes = [];
  let start = first;
  while (start <= last) {
    const alignmentBits = trailingZeros(start, bits);
    const remainingBits = floorLog2(last - start + 1n);
    const blockBits = Math.min(alignmentBits, remainingBits);
    prefixes.push(`${formatter(start)}/${bits - blockBits}`);
    start += 1n << BigInt(blockBits);
  }
  return prefixes;
}


function dumpIpCidrs(reader) {
  if (reader.u8() !== 1) {
    throw new Error("unsupported MRS IP-set version");
  }
  const rangeCount = reader.u64();
  if (rangeCount < 1) throw new Error("invalid empty MRS IP set");
  const prefixes = [];
  for (let index = 0; index < rangeCount; index += 1) {
    let first = bytesToBigInt(reader.bytes(16));
    let last = bytesToBigInt(reader.bytes(16));
    if (last < first) throw new Error("invalid reversed MRS IP range");
    if (isMappedIPv4(first) && isMappedIPv4(last)) {
      first &= 0xffffffffn;
      last &= 0xffffffffn;
      prefixes.push(...rangeToPrefixes(first, last, 32, formatIPv4));
    } else {
      prefixes.push(...rangeToPrefixes(first, last, 128, formatIPv6));
    }
  }
  return prefixes;
}


export function parseDecompressedMrs(buffer, expectedBehavior) {
  const reader = new Reader(buffer);
  if (!reader.bytes(4).equals(Buffer.from([0x4d, 0x52, 0x53, 0x01]))) {
    throw new Error("invalid MRS magic bytes");
  }
  const behavior = reader.u8();
  const expectedByte = expectedBehavior === "domain" ? 0 : expectedBehavior === "ipcidr" ? 1 : -1;
  if (behavior !== expectedByte) {
    throw new Error(`MRS behavior mismatch: file=${behavior}, expected=${expectedBehavior}`);
  }
  reader.u64(); // original rule count; merged sets can contain fewer ranges/keys
  reader.bytes(reader.u64()); // reserved extra data
  return behavior === 0 ? dumpDomains(reader) : dumpIpCidrs(reader);
}


export function dumpMrs(buffer, expectedBehavior) {
  if (typeof zlib.zstdDecompressSync !== "function") {
    throw new Error("Node.js with zstdDecompressSync support is required");
  }
  return parseDecompressedMrs(zlib.zstdDecompressSync(buffer), expectedBehavior);
}


const invokedPath = process.argv[1] ? fs.realpathSync(process.argv[1]) : "";
if (invokedPath === fileURLToPath(import.meta.url)) {
  const [behavior, source, dest] = process.argv.slice(2);
  if (!behavior || !source || !dest) {
    throw new Error("usage: dump_mrs.mjs <domain|ipcidr> <source.mrs> <dest.list>");
  }
  const rules = dumpMrs(fs.readFileSync(source), behavior);
  fs.writeFileSync(dest, `${rules.join("\n")}\n`, "utf8");
}
