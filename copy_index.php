<?php
// 复制 index_v2024.asp 到 index.asp
$source = 'index_v2024.asp';
$dest = 'index.asp';

if (file_exists($source)) {
    if (copy($source, $dest)) {
        echo "成功：index.asp 已创建\n";
        echo "文件大小：" . filesize($dest) . " 字节\n";
    } else {
        echo "错误：复制失败\n";
    }
} else {
    echo "错误：源文件不存在\n";
}
?>
