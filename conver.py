import os
import struct
import time
import io
import csv
from typing import List, NamedTuple

class Entry(NamedTuple):
    word: str
    code: str
    order: int

Table = List[Entry]

def GetUint32(value: int) -> bytes: return struct.pack('<I', value)
def GetUint16(value: int) -> bytes: return struct.pack('<H', value)
def Encode(text: str, encoding: str) -> bytes: return text.encode(encoding)

def Gen(table: Table) -> bytes:
    buf = io.BytesIO()
    stamp = int(time.time())
    buf.write(b"mschxudp\x02\x00`\x00\x01\x00\x00\x00")
    buf.write(GetUint32(0x40))
    buf.write(GetUint32(0x40 + 4 * len(table)))
    buf.write(b"\x00\x00\x00\x00")
    buf.write(GetUint32(len(table)))
    buf.write(GetUint32(stamp))
    buf.write(b"\x00" * 28)
    buf.write(b"\x00" * 4)

    words, codes, sum_ = [], [], 0
    for i, entry in enumerate(table):
        word = Encode(entry.word, "utf-16-le")
        code = Encode(entry.code, "utf-16-le")
        words.append(word)
        codes.append(code)
        if i != len(table) - 1:
            sum_ += len(word) + len(code) + 20
            buf.write(GetUint32(sum_))

    for i, entry in enumerate(table):
        buf.write(b"\x10\x00\x10\x00")
        buf.write(GetUint16(len(codes[i]) + 18))
        buf.write(entry.order.to_bytes(1, byteorder='little'))
        buf.write(b"\x06")
        buf.write(b"\x00" * 4)
        buf.write(GetUint32(stamp))
        buf.write(codes[i])
        buf.write(b"\x00\x00")
        buf.write(words[i])
        buf.write(b"\x00\x00")

    data = buf.getvalue()
    buf.seek(0x18)
    buf.write(GetUint32(len(data)))
    return buf.getvalue()

def SaveToDat(table: Table, output_file: str):
    data = Gen(table)
    with open(output_file, 'wb') as f:
        f.write(data)
    print(f"\n✅ .dat 文件已生成：{output_file}")
    print(f"📊 共转换词条数：{len(table)} 条")

    preview_count = min(5, len(table))
    if preview_count > 0:
        print("🔍 示例词条预览：")
        for entry in table[:preview_count]:
            print(f"  - {entry.word} ({entry.code}) 序号: {entry.order}")

def LoadInputFile(input_file: str) -> Table:
    table = []
    ext = os.path.splitext(input_file)[1].lower()
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start = 0
    if lines and ("候选词位置" in lines[0] or "拼音" in lines[0] or "词语" in lines[0]):
        start = 1

    for line in lines[start:]:
        row = [x.strip() for x in line.strip().split(",")]
        if len(row) != 3:
            print(f"⚠️ 跳过格式错误的行: {line.strip()}")
            continue
        word, code, order = row
        try:
            table.append(Entry(word, code, int(order)))
        except ValueError:
            print(f"⚠️ 跳过无法解析的行: {line.strip()}")
    return table

def main():
    print("🛠️ 微软拼音词库转换（支持 txt/csv → dat）")
    input_file = input("📂 输入文件路径（默认 词库.csv）: ").strip() or "词库.csv"
    output_file = input("📁 输出 .dat 文件路径（默认 微软自定义短语.dat）: ").strip() or "微软自定义短语.dat"

    if not os.path.exists(input_file):
        print(f"❌ 错误：文件 {input_file} 不存在！")
        return

    table = LoadInputFile(input_file)
    if not table:
        print("⚠️ 未读取到有效词条，终止生成。")
        return

    SaveToDat(table, output_file)

if __name__ == "__main__":
    main()
