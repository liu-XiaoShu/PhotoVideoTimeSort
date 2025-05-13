#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# Author: 刘小树
# Description: 全功能媒体文件整理工具
"""
import os, argparse, re, sys
import shutil
import hashlib
import json
import subprocess
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import exifread
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pillow_heif

# 注册HEIF支持
pillow_heif.register_heif_opener()

__version__="V0.1.0"

class MediaOrganizer:
    def __init__(self, inputDir, output_dir, fixed_location=None, config_file='media_config.json'):
        self.inputDir = os.path.expanduser(inputDir)
        self.output_dir = os.path.expanduser(output_dir)
        self.config_file = config_file
        self.md5_records = self.load_config()
        self.geolocator = Nominatim(user_agent="media-organizer-v8")
        self.fixed_location = fixed_location
        self.supported_exts = {
            'image': ['jpg', 'jpeg', 'png', 'heic'],
            'video': ['mp4', 'mov', 'avi', 'mkv']
        }

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'processed_md5': {}}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.md5_records, f, indent=2)

    def calculate_md5(self, file_path):
        """大文件友好的MD5计算"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def extract_date_from_filename(self, filename):
        """支持多种日期格式的智能解析"""
        patterns = [
            # 带时间的格式
            r'(\d{4}[_\-/]\d{2}[_\-/]\d{2}[_\- T]\d{2}:\d{2}:\d{2})',  # 2021-10-02 08:49:00
            r'(\d{4}[_\-/]\d{2}[_\-/]\d{2}[_\-T]\d{6})',              # 2021_10_02_084900
            r'(\d{4}[_\-/]\d{2}[_\-/]\d{2}[_\-T]\d{4})',              # 2021-10-02_0849
            
            # 纯日期格式
            r'(\d{4}[_\-/]\d{2}[_\-/]\d{2})',                         # 2021-10-02 或 2021_10_02
            r'(\d{8})',                                               # 20211002
            r'(\d{4}年\d{1,2}月\d{1,2}日)',                          # 中文日期格式
            r'(IMG_|VID_)(\d{8})',                                    # 系统生成文件名格式
            r'(\d{4}-\d{2}-\d{2})'                                    # ISO日期格式
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                time_str = match.group(0) if pattern.startswith('(IMG') else match.group(1)
                # 统一处理分隔符
                normalized = re.sub(r'[^0-9]', '', time_str[-8:] if 'IMG_' in pattern else time_str)
                
                try:
                    if len(normalized) == 14:  # 完整时间戳
                        return datetime.strptime(normalized, "%Y%m%d%H%M%S")
                    elif len(normalized) == 12:  # 简略时间戳
                        return datetime.strptime(normalized, "%Y%m%d%H%M")
                    elif len(normalized) == 8:   # 纯日期格式
                        return datetime.strptime(normalized, "%Y%m%d").replace(hour=0, minute=0)
                except ValueError:
                    continue
        return None

    def get_metadata(self, file_path):
        """统一元数据提取接口"""
        ext = file_path.split('.')[-1].lower()
        if ext in self.supported_exts['image']:
            return self._get_image_metadata(file_path)
        elif ext in self.supported_exts['video']:
            return self._get_video_metadata(file_path)
        return {}

    def _get_image_metadata(self, file_path):
        """处理图片元数据"""
        try:
            if file_path.lower().endswith(('.heic', 'heif')):
                img = Image.open(file_path)
                return {TAGS[k]: v for k, v in img.getexif().items() if k in TAGS}
            else:
                with open(file_path, 'rb') as f:
                    return exifread.process_file(f, details=False)
        except Exception as e:
            print(f"图片元数据错误: {file_path} - {str(e)}")
            return {}

    def _get_video_metadata(self, file_path):
        """提取视频元数据"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return json.loads(result.stdout)
        except Exception as e:
            print(f"视频元数据错误: {file_path} - {str(e)}")
            return {}

    def get_media_time(self, file_path, metadata):
        """四层时间追溯策略"""
        # 元数据时间优先
        if metadata.get('DateTimeOriginal'):
            try:
                return datetime.strptime(str(metadata['DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
            except ValueError:
                pass
        
        # 视频创建时间
        if metadata.get('format', {}).get('tags', {}).get('creation_time'):
            try:
                return datetime.fromisoformat(metadata['format']['tags']['creation_time'].replace('Z', '+00:00'))
            except ValueError:
                pass

        # 文件名时间解析
        filename_time = self.extract_date_from_filename(os.path.basename(file_path))
        if filename_time:
            return filename_time

        # 文件系统时间降级
        stat = os.stat(file_path)
        return datetime.fromtimestamp(min(stat.st_ctime, stat.st_mtime))

    def get_gps_info(self, metadata):
        """统一GPS解析"""
        if isinstance(metadata, dict):
            return self._parse_video_gps(metadata)
        return self._parse_image_gps(metadata)

    def _parse_image_gps(self, tags):
        """解析图片GPS数据"""
        try:
            lat = self._convert_to_degrees(tags['GPS GPSLatitude'].values)
            lon = self._convert_to_degrees(tags['GPS GPSLongitude'].values)
            if tags.get('GPS GPSLatitudeRef', 'N') == 'S':
                lat = -lat
            if tags.get('GPS GPSLongitudeRef', 'E') == 'W':
                lon = -lon
            return (lat, lon)
        except KeyError:
            return None

    def _parse_video_gps(self, metadata):
        """解析视频GPS数据"""
        try:
            loc_str = metadata['format']['tags'].get('location', '')
            if loc_str:
                parts = loc_str.replace('+', '').split('/')
                return (float(parts[0]), float(parts[1]))
        except Exception:
            return None

    def _convert_to_degrees(self, value):
        """GPS坐标转换"""
        d = float(value[0].num) / value[0].den
        m = float(value[1].num) / value[1].den
        s = float(value[2].num) / value[2].den
        return d + (m / 60.0) + (s / 3600.0)

    def resolve_location(self, gps):
        """带重试机制的地理编码"""
        if self.fixed_location:
            return self.fixed_location
            
        if not gps:
            return "未知地点"
            
        try:
            location = self.geolocator.reverse(f"{gps[0]}, {gps[1]}", language='zh-CN', timeout=10)
            return location.address.split(',')[0]
        except (GeocoderTimedOut, Exception) as e:
            print(f"地理编码失败: {str(e)}")
            return "未知地点"

    def process_file(self, file_path):
        """文件处理核心逻辑"""
        file_md5 = self.calculate_md5(file_path)
        if file_md5 in self.md5_records['processed_md5']:
            print(f"跳过重复文件: {file_path}")
            return

        metadata = self.get_metadata(file_path)
        dt = self.get_media_time(file_path, metadata)
        gps = self.get_gps_info(metadata)
        location = self.resolve_location(gps)

        # 构建目标路径
        ext = os.path.splitext(file_path)[1][1:].lower()
        file_type = '视频' if ext in self.supported_exts['video'] else '图片'
        dest_dir = os.path.join(
            self.output_dir,
            f"{dt.year}年度",
            f"{dt.year}-{dt.month:02d}",
            file_type
        )
        new_name = f"{dt.strftime('%Y-%m-%d-%H:%M')}_{file_md5[:8]}_{location}.{ext}"

        # 执行文件转移
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, new_name)
        if not os.path.exists(dest_path):
            shutil.copy(file_path, dest_path)
            #shutil.move(file_path, dest_path)
            self.md5_records['processed_md5'][file_md5] = dest_path
            print(f"已整理: {dest_path}")

    def scan_directory(self, path):
        """递归扫描目录"""
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                yield from self.scan_directory(entry.path)
            else:
                yield entry.path

    def run(self):
        """主运行流程"""
        try:
            for file_path in self.scan_directory(self.inputDir):
                ext = os.path.splitext(file_path)[1][1:].lower()
                if ext in {e for v in self.supported_exts.values() for e in v}:
                    self.process_file(file_path)
        finally:
            self.save_config()

if __name__ == '__main__':
    update_time = "Update time: 2025-05-13\nauthor: liu-XiaoShu"
    version_info = "\nversion: " + str(__version__) + "\n" + update_time
    tool_description = "这个是一个视频/图片文件整理工具，主要用于家庭相册视频整理"
    parser = argparse.ArgumentParser(description=tool_description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-v', '-V', '--version', action='version', version=version_info,
                        help='Print software version info')
    parser.add_argument('-i', '--inputPath', help='源目录路径')
    parser.add_argument('-o', '--outputPath', default='output', help='输出目录')
    parser.add_argument('-L', '--location', default='未知详情', help='强制使用指定地点/附加信息')
    args = parser.parse_args()

    organizer = MediaOrganizer(
        inputDir=args.inputPath,
        output_dir=args.outputPath,
        fixed_location=args.location
    )
    organizer.run()
