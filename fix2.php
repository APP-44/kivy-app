<?php
$source = 'index_v2024.asp';
$target = 'index.php';

if (file_exists($source)) {
    $content = file_get_contents($source);
    if ($content) {
        $result = file_put_contents($target, $content);
        if ($result) {
            echo "OK: File copied, size = $result\n";
        } else {
            echo "Error: Cannot write\n";
        }
    } else {
        echo "Error: Cannot read source\n";
    }
} else {
    echo "Error: Source not found\n";
}
?>
