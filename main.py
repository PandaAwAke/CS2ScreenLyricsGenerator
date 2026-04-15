import os
import re
import shutil
from PIL import Image, ImageDraw, ImageFont

# ====================== 【全局统一配置：只改这里】 ======================
# 歌词文件配置
LRC_FILE = "lyrics/ENLIGHTENMENT.lrc"

# 路径配置（已完全合一）
TEXTURE_DIR = "materials/abyss/music/enlightenment"     # 对应 content 文件夹
PARTICLE_DIR = "particles/abyss/music/enlightenment"    # 对应 content 文件夹
TEMPLATE_DIR = "templates"      # 无需修改
FINAL_OUTPUT_DIR = "output"     # 输出到的文件夹（当前目录）

# 字体与图片配置
EN_FONT_PATH = "fonts/AkzidenzGrotesk-MediumItalic.otf"     # 英文字体
CN_FONT_PATH = "fonts/AaGuDianKeBenSongYouMoBan-2.ttf"           # 中文字体
EN_DEFAULT_SIZE = 48        # 英文字体默认大小 px
CN_DEFAULT_SIZE = 40        # 中文字体默认大小 px
IMAGE_SIZE_WIDTH = 1024
IMAGE_SIZE_HEIGHT = 512
MAX_WIDTH_RATIO = 0.85      # 最宽可以扩充到多宽比例
Y_PADDING = 12              # 英文中文 竖方向间隔
ENABLE_CHINESE_SCALE_WITH_EN = True    # 开启中文随英文缩放
CN_SCALE_MULTIPLIER = 1              # 中文缩放 = 英文比例 × 这个值

# 粒子与触发器命名配置
IMAGE_PREFIX = "lyric"      # 生成的文件名前缀（vtex、particle）
LYRICS_PARTICLE_PREFIX = "particle_enlightenment"   # 粒子 entity 的前缀
RELAY_ENTITY_NAME = "lyrics_relay_enlightenment"    # 粒子 relay 的前缀
STOP_INTERVAL = 1         # 上一句到下一句之间的默认间隔（播放下一句之前，上一句提前多久停止）
MAX_DURATION = 5.0          # 每句歌词最长显示多久


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
    img = Image.new('RGBA', (IMAGE_SIZE_WIDTH, IMAGE_SIZE_HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    max_w = IMAGE_SIZE_WIDTH * MAX_WIDTH_RATIO

    # 基础字体
    try:
        en_font_base = ImageFont.truetype(EN_FONT_PATH, EN_DEFAULT_SIZE)
        cn_font_base = ImageFont.truetype(CN_FONT_PATH, CN_DEFAULT_SIZE)
    except:
        en_font_base = ImageFont.load_default(size=EN_DEFAULT_SIZE)
        cn_font_base = ImageFont.load_default(size=CN_DEFAULT_SIZE)

    # -------------------------- 英文自动缩放 --------------------------
    e_bbox = draw.textbbox((0, 0), en_text, font=en_font_base)
    e_w = e_bbox[2] - e_bbox[0]
    en_scale = 1.0
    if e_w > max_w:
        en_scale = max_w / e_w

    en_final_size = max(8, int(EN_DEFAULT_SIZE * en_scale))
    en_fnt = ImageFont.truetype(EN_FONT_PATH, en_final_size)

    # -------------------------- 中文随英文联动缩放（新增功能） --------------------------
    if ENABLE_CHINESE_SCALE_WITH_EN:
        cn_scale = en_scale * CN_SCALE_MULTIPLIER
    else:
        # 不联动 → 中文自己独立缩放
        c_bbox = draw.textbbox((0, 0), cn_text, font=cn_font_base)
        c_w = c_bbox[2] - c_bbox[0]
        cn_scale = 1.0
        if c_w > max_w:
            cn_scale = max_w / c_w

    cn_final_size = max(6, int(CN_DEFAULT_SIZE * cn_scale))
    cn_fnt = ImageFont.truetype(CN_FONT_PATH, cn_final_size)

    # 居中排版
    e_b = draw.textbbox((0, 0), en_text, font=en_fnt)
    c_b = draw.textbbox((0, 0), cn_text, font=cn_fnt)
    e_x = (IMAGE_SIZE_WIDTH - (e_b[2]-e_b[0])) // 2
    c_x = (IMAGE_SIZE_WIDTH - (c_b[2]-c_b[0])) // 2
    mid_y = IMAGE_SIZE_HEIGHT // 2
    e_y = mid_y - (e_b[3]-e_b[1]) - Y_PADDING
    c_y = mid_y + Y_PADDING

    draw.text((e_x, e_y), en_text, font=en_fnt, fill=(255,255,255,255))
    draw.text((c_x, c_y), cn_text, font=cn_fnt, fill=(255,255,255,255))
    img.save(save_path, format='TGA')


def batch_build_tga():
    os.makedirs(TEXTURE_DIR, exist_ok=True)
    with open(LRC_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    lyrics = parse_lrc(content)
    valid = 0
    for idx, (time_tag, lines) in enumerate(lyrics):
        if len(lines)>=2:
            en = lines[0]
            cn = lines[1]
            out = f"{TEXTURE_DIR}/{IMAGE_PREFIX}_{idx:03d}.tga"
            make_single_image(en, cn, out)
            valid +=1
    print(f"✅ TGA 生成完成：{valid} 张")
    return valid


def batch_build_tga():
    os.makedirs(TEXTURE_DIR, exist_ok=True)
    with open(LRC_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    lyrics = parse_lrc(content)
    valid = 0
    for idx, (time_tag, lines) in enumerate(lyrics):
        if len(lines)>=2:
            en = lines[0]
            cn = lines[1]
            out = f"{TEXTURE_DIR}/{IMAGE_PREFIX}_{idx:03d}.tga"
            make_single_image(en, cn, out)
            valid +=1
    print(f"✅ TGA 生成完成：{valid} 张")
    return valid


# -------------------------- VTEX / VPCF 生成 --------------------------
def copy_all_tga():
    print(f"🔁 TGA 已直接生成在目标目录，无需复制")
    return True

def generate_vtex_vpcf_files():
    os.makedirs(PARTICLE_DIR, exist_ok=True)
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

    with open(LRC_FILE, 'r', encoding='utf-8') as f:
        lyrics = parse_lrc(f.read())
    total = sum(1 for _, lines in lyrics if len(lines)>=2)

    for i in range(total):
        idx = f"{i:03d}"
        base = f"{IMAGE_PREFIX}_{idx}"

        # VTEX
        tga_path = f"{TEXTURE_DIR}/{base}.tga"
        vtex_content = tpl_vtex.replace("###", tga_path)
        with open(os.path.join(TEXTURE_DIR, f"{base}.vtex"), "w", encoding="utf-8") as f:
            f.write(vtex_content)

        # VPCF
        vtex_resource = f"{TEXTURE_DIR}/{base}.vtex"
        vpcf_content = tpl_vpcf.replace("###", vtex_resource)
        with open(os.path.join(PARTICLE_DIR, f"{base}.vpcf"), "w", encoding="utf-8") as f:
            f.write(vpcf_content)

        # FIX VPCF
        vpcf_resource = f"{PARTICLE_DIR}/{base}.vpcf"
        fix_content = tpl_vpcf_fix.replace("###", vpcf_resource)
        with open(os.path.join(PARTICLE_DIR, f"{base}_fix.vpcf"), "w", encoding="utf-8") as f:
            f.write(fix_content)

        print(f"📄 生成：{base}")

    print("🎉 VTEX + VPCF 生成完毕")

# -------------------------- TRIGGER 生成（新功能） --------------------------
def generate_trigger_file():
    with open(LRC_FILE, 'r', encoding='utf-8') as f:
        lyrics = parse_lrc(f.read())

    valid_entries = []
    for time_tag, lines in lyrics:
        if len(lines) >= 2:
            valid_entries.append((parse_time(time_tag), lines))
    if not valid_entries:
        print("❌ 无有效歌词")
        return

    t0 = valid_entries[0][0]
    rel_times = [(round(t - t0, 1), idx) for idx, (t, _) in enumerate(valid_entries)]
    connections = []

    for idx in range(len(rel_times)):
        t_start, i = rel_times[idx]
        target = f"{LYRICS_PARTICLE_PREFIX}_{i:03d}"

        # Start
        conn_start = f"""
		{{
			sourceEntity = "{RELAY_ENTITY_NAME}"
			output = "OnTrigger"
			targetEntity = "{target}"
			input = "Start"
			param = ""
			ioTargetType = "ENTITY_IO_TARGET_ENTITYNAME_OR_CLASSNAME"
			delay = {t_start:.1f}
			timesToFire = -1
			relayConnection = false
			fromGlobalRelay = false
			m_paramMap = null
		}}"""

        # Stop 逻辑
        if idx < len(rel_times) - 1:
            t_next = rel_times[idx+1][0]
            t_stop = t_next - STOP_INTERVAL
        else:
            t_stop = t_start + MAX_DURATION

        duration = t_stop - t_start
        if duration > MAX_DURATION:
            t_stop = t_start + MAX_DURATION
        t_stop = round(t_stop, 1)

        conn_stop = f"""
		{{
			sourceEntity = "{RELAY_ENTITY_NAME}"
			output = "OnTrigger"
			targetEntity = "{target}"
			input = "Stop"
			param = ""
			ioTargetType = "ENTITY_IO_TARGET_ENTITYNAME_OR_CLASSNAME"
			delay = {t_stop:.1f}
			timesToFire = -1
			relayConnection = false
			fromGlobalRelay = false
			m_paramMap = null
		}}"""

        connections.append(conn_start.strip())
        connections.append(conn_stop.strip())

    # 拼接输出
    header = '''<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
{
	connections =\n	['''
    footer = "\n\t]\n}"

    final = header + ",\n".join(connections) + footer
    out_path = f"{RELAY_ENTITY_NAME}-trigger.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final)
    print(f"✅ TRIGGER 文件已生成：{out_path}")
    return out_path


# -------------------------- 最终打包：移动全部内容到 output --------------------------
def move_to_final_output(trigger_file):
    print(f"\n📦 开始打包所有内容到：{FINAL_OUTPUT_DIR}")

    # 清空并重建输出目录
    if os.path.exists(FINAL_OUTPUT_DIR):
        shutil.rmtree(FINAL_OUTPUT_DIR)
    os.makedirs(FINAL_OUTPUT_DIR)

    # 移动目录
    if os.path.exists("materials"):
        shutil.move("materials", os.path.join(FINAL_OUTPUT_DIR, "materials"))
    if os.path.exists("particles"):
        shutil.move("particles", os.path.join(FINAL_OUTPUT_DIR, "particles"))

    # 移动 trigger.txt
    if os.path.exists(trigger_file):
        shutil.move(trigger_file, os.path.join(FINAL_OUTPUT_DIR, trigger_file))

    print(f"✅ 所有文件已打包到：{FINAL_OUTPUT_DIR}")


# -------------------------- 主执行 --------------------------
def main():
    print("===== 1. 生成歌词TGA =====")
    batch_build_tga()

    print("\n===== 2. 生成VTEX + VPCF =====")
    generate_vtex_vpcf_files()

    print("\n===== 3. 生成TRIGGER =====")
    trigger_file = generate_trigger_file()

    print("\n===== 4. 打包所有内容到 output 文件夹 =====")
    move_to_final_output(trigger_file)

    print("\n🎉 全部任务完成！")

if __name__ == "__main__":
    main()