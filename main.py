import os
import re
import shutil
from PIL import Image, ImageDraw, ImageFont

# ====================== 【全局统一配置：只改这里】 ======================
# 歌词文件配置
LRC_FILE = "lyrics/ENLIGHTENMENT.lrc"  # LRC歌词文件路径

# 路径配置
OUTPUT_TGA_DIR = "lyrics_tga/ENLIGHTENMENT"  # TGA生成输出目录
TEXTURE_DIR = "materials/abyss/music/enlightenment"  # vtex存放目录（TGA会被复制到这里）
PARTICLE_DIR = "particles/abyss/music/enlightenment"  # vpcf + fix 存放目录
TEMPLATE_DIR = "templates"  # 模板文件夹

# 字体与图片配置
EN_FONT_PATH = "fonts/AkzidenzGrotesk-MediumItalic.otf"  # 英文字体路径
CN_FONT_PATH = "fonts/SourceHanSansCN-Medium.otf"  # 中文字体路径
EN_DEFAULT_SIZE = 80  # 英文默认大小
CN_DEFAULT_SIZE = 48  # 中文默认大小
IMAGE_SIZE_WIDTH = 1024  # 画布宽度
IMAGE_SIZE_HEIGHT = 512  # 画布高度
MAX_WIDTH_RATIO = 0.85  # 文字最大占宽度比例
Y_PADDING = 24  # 中英文竖向间隔

# 文件名配置
IMAGE_PREFIX = "lyric"  # 文件名前缀 lyric_000


# ======================================================================

# -------------------------- TGA生成相关函数 --------------------------
def parse_lrc(lrc_text):
    pattern = re.compile(r'\[(\d{2}:\d{2}(?:\.\d+)?)](.*)')
    lyric_map = {}
    for line in lrc_text.strip().split('\n'):
        m = pattern.match(line.strip())
        if m:
            time_tag = m.group(1)
            content = m.group(2).strip()
            if time_tag not in lyric_map:
                lyric_map[time_tag] = []
            lyric_map[time_tag].append(content)
    sorted_list = sorted(lyric_map.items(), key=lambda x: parse_time(x[0]))
    return sorted_list


def parse_time(time_str):
    m, s = time_str.split(':')
    return float(m) * 60 + float(s)


def make_single_image(en_text, cn_text, save_path):
    img = Image.new('RGBA', (IMAGE_SIZE_WIDTH, IMAGE_SIZE_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    max_w = IMAGE_SIZE_WIDTH * MAX_WIDTH_RATIO

    # 加载字体
    try:
        en_font = ImageFont.truetype(EN_FONT_PATH, EN_DEFAULT_SIZE)
        cn_font = ImageFont.truetype(CN_FONT_PATH, CN_DEFAULT_SIZE)
    except:
        en_font = ImageFont.load_default(size=EN_DEFAULT_SIZE)
        cn_font = ImageFont.load_default(size=CN_DEFAULT_SIZE)

    # 英文自适应
    e_w = draw.textbbox((0, 0), en_text, font=en_font)[2]
    if e_w > max_w:
        scale = max_w / e_w
        en_font = ImageFont.truetype(EN_FONT_PATH, int(EN_DEFAULT_SIZE * scale))

    # 中文自适应
    c_w = draw.textbbox((0, 0), cn_text, font=cn_font)[2]
    if c_w > max_w:
        scale = max_w / c_w
        cn_font = ImageFont.truetype(CN_FONT_PATH, int(CN_DEFAULT_SIZE * scale))

    # 居中排版
    e_b = draw.textbbox((0, 0), en_text, font=en_font)
    c_b = draw.textbbox((0, 0), cn_text, font=cn_font)
    e_x = (IMAGE_SIZE_WIDTH - (e_b[2] - e_b[0])) // 2
    c_x = (IMAGE_SIZE_WIDTH - (c_b[2] - c_b[0])) // 2
    mid_y = IMAGE_SIZE_HEIGHT // 2
    e_y = mid_y - (e_b[3] - e_b[1]) - Y_PADDING
    c_y = mid_y + Y_PADDING

    draw.text((e_x, e_y), en_text, font=en_font, fill=(255, 255, 255, 255))
    draw.text((c_x, c_y), cn_text, font=cn_font, fill=(255, 255, 255, 255))
    img.save(save_path, format='TGA')


def batch_build_tga():
    """批量生成TGA图片"""
    os.makedirs(OUTPUT_TGA_DIR, exist_ok=True)
    with open(LRC_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    lyrics = parse_lrc(content)
    valid_count = 0
    for idx, (time_tag, lines) in enumerate(lyrics):
        if len(lines) >= 2:
            en = lines[0]
            cn = lines[1]
            out = f"{OUTPUT_TGA_DIR}/{IMAGE_PREFIX}_{idx:03d}.tga"
            make_single_image(en, cn, out)
            valid_count += 1
    print(f"✅ TGA图片生成完成！共 {valid_count} 张")
    return valid_count


# -------------------------- VTEX/VPCF生成相关函数 --------------------------
def get_lyric_count(lrc_path):
    """统计有多少句歌词（中英一对算一句）"""
    count = 0
    try:
        with open(lrc_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        time_map = {}
        for line in lines:
            line = line.strip()
            if line.startswith("[") and "]" in line:
                time_part = line.split("]")[0] + "]"
                if time_part not in time_map:
                    time_map[time_part] = 0
                time_map[time_part] += 1

        for t, cnt in time_map.items():
            if cnt >= 2:
                count += 1
    except Exception as e:
        print(f"⚠️ 读取歌词失败：{e}，默认按TGA文件数量生成")
        tga_count = len([f for f in os.listdir(OUTPUT_TGA_DIR) if f.lower().endswith(".tga")])
        return tga_count
    return count


def copy_all_tga():
    """预处理：把 TGA_DIR 里所有 .tga 复制到 TEXTURE_DIR"""
    print(f"🔁 预处理：开始复制 TGA 从 {OUTPUT_TGA_DIR} → {TEXTURE_DIR}")

    if not os.path.exists(OUTPUT_TGA_DIR):
        print(f"❌ 错误：TGA 目录 {OUTPUT_TGA_DIR} 不存在！")
        return False

    os.makedirs(TEXTURE_DIR, exist_ok=True)
    copied = 0

    for filename in os.listdir(OUTPUT_TGA_DIR):
        if filename.lower().endswith(".tga"):
            src = os.path.join(OUTPUT_TGA_DIR, filename)
            dst = os.path.join(TEXTURE_DIR, filename)
            shutil.copy2(src, dst)
            copied += 1

    print(f"✅ TGA 复制完成：共 {copied} 张")
    return True


def generate_vtex_vpcf_files():
    """生成VTEX和VPCF相关文件"""
    # 第一步：复制所有TGA
    if not copy_all_tga():
        return

    # 创建目录
    os.makedirs(PARTICLE_DIR, exist_ok=True)

    # 读取模板
    try:
        with open(f"{TEMPLATE_DIR}/example.vtex", "r", encoding="utf-8") as f:
            tpl_vtex = f.read()
        with open(f"{TEMPLATE_DIR}/example.vpcf", "r", encoding="utf-8") as f:
            tpl_vpcf = f.read()
        with open(f"{TEMPLATE_DIR}/example-fix.vpcf", "r", encoding="utf-8") as f:
            tpl_vpcf_fix = f.read()
    except FileNotFoundError as e:
        print(f"❌ 模板缺失：{e}")
        return

    # 获取歌词数量
    total = get_lyric_count(LRC_FILE)
    print(f"✅ 检测到 {total} 句歌词，开始生成粒子文件...")

    # 批量生成
    for i in range(total):
        idx = f"{i:03d}"
        base = f"{IMAGE_PREFIX}_{idx}"

        # ========== 1. 生成 VTEX ==========
        tga_path = f"{TEXTURE_DIR}/{base}.tga"
        vtex_content = tpl_vtex.replace("###", tga_path)
        vtex_path = os.path.join(TEXTURE_DIR, f"{base}.vtex")
        with open(vtex_path, "w", encoding="utf-8") as f:
            f.write(vtex_content)

        # ========== 2. 生成 VPCF ==========
        vtex_resource = f"{TEXTURE_DIR}/{base}.vtex"
        vpcf_content = tpl_vpcf.replace("###", vtex_resource)
        vpcf_path = os.path.join(PARTICLE_DIR, f"{base}.vpcf")
        with open(vpcf_path, "w", encoding="utf-8") as f:
            f.write(vpcf_content)

        # ========== 3. 生成 VPCF-FIX ==========
        vpcf_resource = f"{PARTICLE_DIR}/{base}.vpcf"
        vpcf_fix_content = tpl_vpcf_fix.replace("###", vpcf_resource)
        vpcf_fix_path = os.path.join(PARTICLE_DIR, f"{base}_fix.vpcf")
        with open(vpcf_fix_path, "w", encoding="utf-8") as f:
            f.write(vpcf_fix_content)

        print(f"📄 已生成：{base}")

    print("\n🎉 【VTEX/VPCF文件生成完成】")
    print(f"📁 TGA 已复制 → {TEXTURE_DIR}")
    print(f"📁 VTEX 文件 → {TEXTURE_DIR}")
    print(f"📁 VPCF 粒子 → {PARTICLE_DIR}")
    print(f"📁 VPCF_FIX  → {PARTICLE_DIR}")


# -------------------------- 主执行函数 --------------------------
def main():
    """主流程：先生成TGA，再生成VTEX/VPCF"""
    print("===== 开始执行TGA图片生成 =====")
    batch_build_tga()

    print("\n===== 开始执行VTEX/VPCF文件生成 =====")
    generate_vtex_vpcf_files()

    print("\n===== 所有任务执行完成 =====")


if __name__ == "__main__":
    main()