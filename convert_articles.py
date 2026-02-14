#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章转换脚本：将my_articles中的Markdown文章转换为Hugo Stack主题格式
使用Page Bundles结构（每个文章一个文件夹，包含index.md和图片资源）
"""

import os
import re
import shutil
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime

# 设置输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 项目根目录
ROOT_DIR = Path(__file__).parent
MY_ARTICLES_DIR = ROOT_DIR / "my_articles"
CONTENT_DIR = ROOT_DIR / "content" / "post"

# 分类映射
CATEGORY_MAP = {
    "其它技术文章": "技术杂谈",
    "新齐民要术：电脑维修技艺精解": "电脑维修"
}

# 电脑维修文章白名单（从README.md提取）
REPAIR_ARTICLE_WHITELIST = [
    "1望闻问切理论.md",
    "2浅谈硬件维修.md",
    "3系统故障诊断与修复.md",
    "4软件警告弹窗与兼容性问题.md",
    "5预防与清除恶意软件.md",
    "6网络与通信问题.md",
    "7驱动与硬件协同问题.md",
    "8数据恢复与备份策略.md",
    "9系统优化与性能调校.md",
    "10Windows蓝屏问题处理指南.md",
    "12桌面图标变白色了.md",
    "13如何安装office.md",
    "15连接显示器专题.md",
    "22压缩与解压缩专题.md",
    "23文件传输专题.md",
    "24打印机专题.md",
    "25安装系统进阶专题.md",
]

def get_file_date(file_path):
    """获取文件的修改时间作为日期"""
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

def get_title_from_filename(filename):
    """从文件名提取标题（移除开头的数字和扩展名）"""
    name = Path(filename).stem
    # 移除开头的数字
    name = re.sub(r'^\d+', '', name)
    return name.strip()

def generate_slug(filename):
    """生成URL友好的slug"""
    name = Path(filename).stem
    # 移除开头的数字
    name = re.sub(r'^\d+', '', name)
    # 清理特殊字符
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\-]', '-', name)
    name = re.sub(r'-+', '-', name).strip('-')
    return name

def fix_image_paths(content):
    """修复图片路径为相对路径"""
    def replace_image(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        
        # URL解码路径
        img_path = urllib.parse.unquote(img_path)
        
        # 提取文件名
        if '/' in img_path:
            img_name = img_path.split('/')[-1]
        else:
            img_name = Path(img_path).name
        
        # 使用相对路径（相对于文章目录）
        return f'![{alt_text}]({img_name})'
    
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    content = re.sub(pattern, replace_image, content)
    
    return content

def convert_article(src_path, category, dest_base_dir):
    """转换单篇文章为Page Bundle格式"""
    with open(src_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if len(content.strip()) < 50:
        print(f"跳过空文件: {src_path.name}")
        return None
    
    # 使用文件名作为标题（移除开头的数字）
    title = get_title_from_filename(src_path.name)
    slug = generate_slug(src_path.name)
    date = get_file_date(src_path)
    
    # 不再移除第一个标题，保留所有内容
    # 修复图片路径
    content = fix_image_paths(content)
    
    # 创建文章目录（Page Bundle）
    article_dir = dest_base_dir / slug
    article_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建front matter
    front_matter = f"""---
title: "{title}"
slug: "{slug}"
date: {date}
categories: 
    - {category}
tags: []
draft: false
---
"""
    
    new_content = front_matter + content
    
    # 写入index.md
    dest_path = article_dir / "index.md"
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"已转换: {src_path.name} -> {slug}/index.md (标题: {title})")
    
    # 复制资源文件夹中的图片到文章目录
    asset_folder_name = src_path.stem + ".assets"
    asset_src_dir = src_path.parent / asset_folder_name
    
    if asset_src_dir.exists() and asset_src_dir.is_dir():
        for img_file in asset_src_dir.iterdir():
            if img_file.is_file():
                shutil.copy2(img_file, article_dir / img_file.name)
        print(f"  复制资源: {asset_folder_name} -> {slug}/")
    
    return slug

def main():
    print("开始转换文章（Page Bundle格式）...")
    print(f"源目录: {MY_ARTICLES_DIR}")
    print(f"目标目录: {CONTENT_DIR}")
    print("-" * 50)
    
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_articles = 0
    
    for category_dir in MY_ARTICLES_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        
        category_name = category_dir.name
        hugo_category = CATEGORY_MAP.get(category_name, category_name)
        
        print(f"\n处理分类: {category_name} -> {hugo_category}")
        
        for md_file in sorted(category_dir.glob("*.md")):
            # 跳过README.md
            if md_file.name.lower() == "readme.md":
                continue
            
            # 如果是电脑维修分类，检查白名单
            if category_name == "新齐民要术：电脑维修技艺精解":
                if md_file.name not in REPAIR_ARTICLE_WHITELIST:
                    print(f"跳过（不在白名单中）: {md_file.name}")
                    continue
            
            result = convert_article(md_file, hugo_category, CONTENT_DIR)
            if result:
                total_articles += 1
    
    print("\n" + "=" * 50)
    print(f"转换完成！共转换 {total_articles} 篇文章")
    print(f"文章位置: {CONTENT_DIR}")

if __name__ == "__main__":
    main()
