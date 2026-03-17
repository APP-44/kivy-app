<?php
/**
 * 高端员工档案展示页面
 * 支持动态数据加载
 */

// 数据库配置
$db_config = array(
    'host' => 'localhost',
    'user' => 'shizhnegwheng',
    'pass' => '63zskcx5m8kk',
    'name' => 'shizhnegwheng'
);

// 连接数据库
function getDB() {
    global $db_config;
    $conn = new mysqli($db_config['host'], $db_config['user'], $db_config['pass'], $db_config['name']);
    if ($conn->connect_error) {
        die("数据库连接失败");
    }
    $conn->query("SET NAMES utf8mb4");
    return $conn;
}

// 获取员工信息
$id = isset($_GET['id']) ? intval($_GET['id']) : 0;
$employee = null;

if ($id > 0) {
    $conn = getDB();
    $stmt = $conn->prepare("SELECT * FROM employees WHERE id = ? AND status = '在职'");
    $stmt->bind_param("i", $id);
    $stmt->execute();
    $result = $stmt->get_result();
    $employee = $result->fetch_assoc();
    $stmt->close();
    $conn->close();
}

// 如果没有找到员工，显示默认信息或列表
if (!$employee) {
    header("Location: employee.php");
    exit;
}

// 解析技能
$skills = $employee['skills'] ? explode(',', $employee['skills']) : array();
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title><?php echo htmlspecialchars($employee['name']); ?> - 专业家政服务</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
        
        body {
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding-bottom: 40px;
        }
        
        /* 顶部导航 */
        .nav-bar {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-bar a {
            color: white;
            text-decoration: none;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .company-logo {
            font-weight: bold;
            font-size: 16px;
        }
        
        /* 头部区域 */
        .header {
            padding: 40px 20px 80px;
            text-align: center;
            color: white;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        
        .header .subtitle {
            font-size: 16px;
            opacity: 0.9;
        }
        
        /* 主容器 */
        .container {
            max-width: 480px;
            margin: -60px auto 0;
            padding: 0 20px;
            position: relative;
            z-index: 10;
        }
        
        /* 卡片样式 */
        .card {
            background: rgba(255, 255, 255, 0.98);
            border-radius: 24px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        /* 个人资料区 */
        .profile-header {
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }
        
        .photo-box {
            position: relative;
            flex-shrink: 0;
        }
        
        .photo {
            width: 120px;
            height: 160px;
            border-radius: 20px;
            object-fit: cover;
            border: 4px solid white;
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        .verified-badge {
            position: absolute;
            bottom: -5px;
            right: -5px;
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
            border: 3px solid white;
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
        }
        
        .profile-info {
            flex: 1;
        }
        
        .name-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }
        
        .name {
            font-size: 28px;
            font-weight: 700;
            color: #1f2937;
        }
        
        .age {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }
        
        .tag {
            background: #f3f4f6;
            color: #4b5563;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
        }
        
        .rating-box {
            display: flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 8px 16px;
            border-radius: 12px;
            width: fit-content;
        }
        
        .stars {
            color: #f59e0b;
            font-size: 16px;
        }
        
        .rating-text {
            font-weight: 600;
            color: #92400e;
            font-size: 14px;
        }
        
        /* 信息网格 */
        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-top: 20px;
        }
        
        .info-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px;
            background: #f9fafb;
            border-radius: 16px;
            transition: all 0.3s;
        }
        
        .info-item:hover {
            background: #f3f4f6;
            transform: translateY(-2px);
        }
        
        .info-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
        }
        
        .info-content {
            flex: 1;
        }
        
        .info-label {
            font-size: 12px;
            color: #9ca3af;
            margin-bottom: 4px;
        }
        
        .info-value {
            font-size: 15px;
            font-weight: 600;
            color: #1f2937;
        }
        
        /* 技能标签 */
        .skills-section {
            margin-top: 20px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .section-title i {
            color: #667eea;
        }
        
        .skills-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .skill-tag {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        /* 个人简介 */
        .intro-section {
            margin-top: 20px;
        }
        
        .intro-text {
            color: #4b5563;
            line-height: 1.8;
            font-size: 15px;
            text-align: justify;
        }
        
        /* 统计信息 */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 20px;
        }
        
        .stat-item {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            border-radius: 16px;
        }
        
        .stat-number {
            font-size: 28px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 13px;
            color: #6b7280;
            margin-top: 4px;
        }
        
        /* 底部按钮 */
        .action-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 24px;
        }
        
        .btn {
            padding: 16px 24px;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
            box-shadow: 0 8px 25px rgba(34, 197, 94, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(34, 197, 94, 0.4);
        }
        
        .btn-secondary {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
        }
        
        .btn-secondary:hover {
            background: #667eea;
            color: white;
        }
        
        /* 页脚 */
        .footer {
            text-align: center;
            padding: 30px 20px;
            color: rgba(255,255,255,0.8);
            font-size: 13px;
        }
        
        .footer a {
            color: white;
            text-decoration: none;
        }
        
        /* 加载动画 */
        .loading {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: opacity 0.5s;
        }
        
        .loading.hide {
            opacity: 0;
            pointer-events: none;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* 响应式 */
        @media (max-width: 480px) {
            .header h1 { font-size: 28px; }
            .name { font-size: 24px; }
            .photo { width: 100px; height: 133px; }
            .info-grid { grid-template-columns: 1fr; }
            .stats-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <!-- 加载动画 -->
    <div class="loading" id="loading">
        <div class="spinner"></div>
    </div>
    
    <!-- 导航栏 -->
    <nav class="nav-bar">
        <a href="/" class="company-logo">
            <i class="fas fa-home"></i> 嘉美净家政
        </a>
        <a href="employee.php">
            <i class="fas fa-users"></i> 员工列表
        </a>
    </nav>
    
    <!-- 头部 -->
    <header class="header">
        <div class="header-content">
            <h1><?php echo htmlspecialchars($employee['name']); ?></h1>
            <p class="subtitle">专业家政服务人员</p>
        </div>
    </header>
    
    <!-- 主内容 -->
    <div class="container">
        <!-- 个人资料卡 -->
        <div class="card">
            <div class="profile-header">
                <div class="photo-box">
                    <?php if ($employee['photo_path'] && file_exists($employee['photo_path'])): ?>
                        <img src="<?php echo $employee['photo_path']; ?>" alt="<?php echo $employee['name']; ?>" class="photo">
                    <?php else: ?>
                        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 160'%3E%3Crect fill='%23f3f4f6' width='120' height='160'/%3E%3Ctext x='50%25' y='50%25' font-size='40' fill='%239ca3af' text-anchor='middle' dy='.3em'%3E👤%3C/text%3E%3C/svg%3E" alt="默认头像" class="photo">
                    <?php endif; ?>
                    <div class="verified-badge">
                        <i class="fas fa-check"></i>
                    </div>
                </div>
                
                <div class="profile-info">
                    <div class="name-row">
                        <span class="name"><?php echo htmlspecialchars($employee['name']); ?></span>
                        <?php if ($employee['age']): ?>
                            <span class="age"><?php echo $employee['age']; ?>岁</span>
                        <?php endif; ?>
                    </div>
                    
                    <div class="tags">
                        <span class="tag"><i class="fas fa-star"></i> 认证员工</span>
                        <span class="tag"><i class="fas fa-shield-alt"></i> 背景已审核</span>
                    </div>
                    
                    <div class="rating-box">
                        <span class="stars">⭐ <?php echo $employee['rating'] ?: '5.0'; ?></span>
                        <span class="rating-text"><?php echo $employee['review_count'] ?: '0'; ?>条好评</span>
                    </div>
                </div>
            </div>
            
            <!-- 统计信息 -->
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-number"><?php echo $employee['work_years'] ?: '0'; ?></div>
                    <div class="stat-label">年经验</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number"><?php echo $employee['review_count'] ?: '0'; ?></div>
                    <div class="stat-label">服务次数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">98%</div>
                    <div class="stat-label">好评率</div>
                </div>
            </div>
        </div>
        
        <!-- 详细信息卡 -->
        <div class="card">
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-icon">
                        <i class="fas fa-map-marker-alt"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">籍贯</div>
                        <div class="info-value">四川绵阳</div>
                    </div>
                </div>
                
                <div class="info-item">
                    <div class="info-icon">
                        <i class="fas fa-graduation-cap"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">学历</div>
                        <div class="info-value">高中</div>
                    </div>
                </div>
                
                <div class="info-item">
                    <div class="info-icon">
                        <i class="fas fa-heart"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">婚姻状况</div>
                        <div class="info-value">已婚</div>
                    </div>
                </div>
                
                <div class="info-item">
                    <div class="info-icon">
                        <i class="fas fa-baby"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">子女情况</div>
                        <div class="info-value">已育</div>
                    </div>
                </div>
            </div>
            
            <!-- 技能标签 -->
            <?php if (!empty($skills)): ?>
            <div class="skills-section">
                <h3 class="section-title">
                    <i class="fas fa-tools"></i> 专业技能
                </h3>
                <div class="skills-list">
                    <?php foreach ($skills as $skill): ?>
                        <span class="skill-tag"><?php echo htmlspecialchars(trim($skill)); ?></span>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endif; ?>
            
            <!-- 个人简介 -->
            <div class="intro-section">
                <h3 class="section-title">
                    <i class="fas fa-user-circle"></i> 个人简介
                </h3>
                <p class="intro-text">
                    <?php echo htmlspecialchars($employee['name']); ?>是嘉美净家政的专业服务人员，
                    拥有<?php echo $employee['work_years'] ?: '多'; ?>年家政服务经验。
                    擅长<?php echo $employee['skills'] ?: '家庭保洁、育儿护理'; ?>，
                    工作认真负责，深受客户好评。
                    期待为您提供优质的家政服务！
                </p>
            </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="action-buttons">
            <a href="tel:18081246654" class="btn btn-primary">
                <i class="fas fa-phone"></i> 立即预约
            </a>
            <a href="employee.php" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> 返回列表
            </a>
        </div>
    </div>
    
    <!-- 页脚 -->
    <footer class="footer">
        <p>四川嘉美净清洁服务有限公司</p>
        <p>服务热线：180-8124-6654 | <a href="/">返回首页</a></p>
    </footer>
    
    <script>
        // 页面加载完成后隐藏加载动画
        window.addEventListener('load', function() {
            setTimeout(function() {
                document.getElementById('loading').classList.add('hide');
            }, 500);
        });
    </script>
</body>
</html>
