import os, struct, time, io, logging
from typing import List, NamedTuple

class Entry(NamedTuple):
    word: str
    code: str
    order: int

def GetUint32(value: int) -> bytes: return struct.pack('<I', value)
def GetUint16(value: int) -> bytes: return struct.pack('<H', value)
def Encode(text: str, encoding: str = "utf-16-le") -> bytes: return text.encode(encoding)

def Gen(table: List[Entry]) -> bytes:
    buf = io.BytesIO()
    stamp = int(time.time())
    buf.write(b"mschxudp\x02\x00`\x00\x01\x00\x00\x00")
    buf.write(GetUint32(0x40))
    buf.write(GetUint32(0x40 + 4 * len(table)))
    buf.write(b"\x00\x00\x00\x00")
    buf.write(GetUint32(len(table)))
    buf.write(GetUint32(stamp))
    buf.write(b"\x00" * 28 + b"\x00" * 4)

    words, codes, offset = [], [], 0
    for i, entry in enumerate(table):
        word = Encode(entry.word)
        code = Encode(entry.code)
        words.append(word)
        codes.append(code)
        if i != len(table) - 1:
            offset += len(word) + len(code) + 20
            buf.write(GetUint32(offset))

    for i, entry in enumerate(table):
        buf.write(b"\x10\x00\x10\x00")
        buf.write(GetUint16(len(codes[i]) + 18))
        buf.write(entry.order.to_bytes(1, "little"))
        buf.write(b"\x06" + b"\x00" * 4)
        buf.write(GetUint32(stamp))
        buf.write(codes[i] + b"\x00\x00")
        buf.write(words[i] + b"\x00\x00")

    data = buf.getvalue()
    buf.seek(0x18)
    buf.write(GetUint32(len(data)))
    return buf.getvalue()

def LoadInputFile(input_file: str) -> List[Entry]:
    table = []
    skipped = 0
    ext = os.path.splitext(input_file)[1].lower()
    encoding = "utf-8"

    try:
        with open(input_file, "r", encoding=encoding) as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        encoding = "gbk"
        with open(input_file, "r", encoding=encoding) as f:
            lines = f.readlines()

    start = 0
    if lines and any(k in lines[0] for k in ["词组", "拼音", "候选词位置"]):
        start = 1

    for line in lines[start:]:
        row = [x.strip() for x in line.strip().split(",")]
        if len(row) != 3:
            logging.warning(f"⚠️ 跳过格式错误行: {line.strip()}")
            skipped += 1
            continue
        try:
            word, code, order = row
            table.append(Entry(word, code, int(order)))
        except ValueError:
            logging.warning(f"⚠️ 跳过无法解析行: {line.strip()}")
            skipped += 1

    print(f"\n📥 已读取词条：{len(table)} 条")
    if skipped:
        print(f"⚠️ 跳过无效行：{skipped} 条")
    return table

def SaveToDat(table: List[Entry], output_file: str):
    data = Gen(table)
    with open(output_file, "wb") as f:
        f.write(data)
    print(f"\n✅ .dat 文件已生成：{output_file}")
    print(f"📊 共转换词条数：{len(table)} 条")

    preview_count = min(5, len(table))
    if preview_count > 0:
        print("🔍 示例词条预览：")
        for entry in table[:preview_count]:
            print(f"  - {entry.word} ({entry.code}) 序号: {entry.order}")

def main():
    logging.basicConfig(level=logging.WARNING)
    print("🛠️ 微软拼音词库转换工具")

    while True:
        input_file = input("📂 输入词库文件路径（默认 词库.csv）: ").strip() or "词库.csv"
        # 获取输入文件所在目录
        input_dir = os.path.dirname(os.path.abspath(input_file))
        default_output = os.path.join(input_dir, "微软自定义短语.dat")
        output_file = input(f"📁 输出.dat文件路径（默认 {default_output}）: ").strip() or default_output

        if not os.path.exists(input_file):
            print(f"❌ 错误：文件不存在 → {input_file}")
            continue  # 回到开头重新输入

        table = LoadInputFile(input_file)
        if not table:
            print("⚠️ 未读取到有效词条，终止生成。")
            continue  # 回到开头重新输入

        SaveToDat(table, output_file)
        break  # 成功后跳出循环



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 程序发生错误：{e}")
    finally:
        input("\n📌 按回车键退出程序...")
