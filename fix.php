<?php
// 修复首页问题
// 读取 index_v2024.asp 的内容
$source_file = 'index_v2024.asp';
$target_file = 'index.php';

if (!file_exists($source_file)) {
    echo "错误：源文件 $source_file 不存在\n";
    exit;
}

$content = file_get_contents($source_file);
if ($content === false) {
    echo "错误：无法读取源文件\n";
    exit;
}

echo "源文件大小：" . strlen($content) . " 字节\n";

// 将 ASP 代码中的特定部分替换为 PHP 兼容的
// 主要是替换 <%=...%> 为 <?php echo ...?>
$content = preg_replace('/<%=(.*?)%>/', '<?php echo $1; ?>', $content);
$content = preg_replace('/<%(.*?)%>/s', '<?php $1 ?>', $content);

// 写入 index.php
$result = file_put_contents($target_file, $content);
if ($result === false) {
    echo "错误：无法写入 $target_file\n";
    exit;
}

echo "成功：$target_file 已更新\n";
echo "新文件大小：$result 字节\n";
?>
