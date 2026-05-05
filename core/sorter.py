from typing import List, Dict


class Sorter:
    """图片排序器"""

    def sort_by_filename(self, images: List[Dict]) -> List[Dict]:
        """按文件名排序"""
        return sorted(images, key=lambda x: x['filename'])

    def move_image(self, images: List[Dict], from_index: int, to_index: int) -> List[Dict]:
        """移动图片位置"""
        if from_index < 0 or from_index >= len(images):
            return images
        if to_index < 0 or to_index >= len(images):
            return images

        result = images.copy()
        image = result.pop(from_index)
        result.insert(to_index, image)
        return result

    def swap_images(self, images: List[Dict], index1: int, index2: int) -> List[Dict]:
        """交换两张图片的位置"""
        if index1 < 0 or index1 >= len(images):
            return images
        if index2 < 0 or index2 >= len(images):
            return images

        result = images.copy()
        result[index1], result[index2] = result[index2], result[index1]
        return result

    def remove_image(self, images: List[Dict], index: int) -> List[Dict]:
        """删除指定位置的图片"""
        if index < 0 or index >= len(images):
            return images

        result = images.copy()
        result.pop(index)
        return result
