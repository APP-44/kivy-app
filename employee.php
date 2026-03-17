<?php
/**
 * 员工电子名片展示页面
 * 网址: scjmj.cn/employee.php?id=X
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
        die("数据库连接失败: " . $conn->connect_error);
    }
    $conn->query("SET NAMES utf8mb4");
    return $conn;
}

// 获取所有在职员工
function getEmployees($search = "") {
    $conn = getDB();
    $sql = "SELECT id, name, age, work_years, skills, photo_path, rating, review_count 
            FROM employees 
            WHERE status = '在职'";
    
    if ($search) {
        $search = $conn->real_escape_string($search);
        $sql .= " AND (name LIKE '%$search%' OR skills LIKE '%$search%')";
    }
    
    $sql .= " ORDER BY rating DESC, work_years DESC";
    
    $result = $conn->query($sql);
    $employees = array();
    while ($row = $result->fetch_assoc()) {
        $employees[] = $row;
    }
    $conn->close();
    return $employees;
}

// 获取单个员工详情
function getEmployee($id) {
    $conn = getDB();
    $id = intval($id);
    $sql = "SELECT * FROM employees WHERE id = $id";
    $result = $conn->query($sql);
    $employee = $result->fetch_assoc();
    $conn->close();
    return $employee;
}

// 路由处理
$id = isset($_GET['id']) ? intval($_GET['id']) : 0;
$is_detail = $id > 0;
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $is_detail ? '员工档案' : '员工风采'; ?> - 四川嘉美净清洁服务有限公司</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        /* 导航栏 */
        .navbar {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .navbar-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar-brand {
            color: white;
            font-size: 20px;
            font-weight: 600;
            text-decoration: none;
        }
        .navbar-links a {
            color: white;
            text-decoration: none;
            margin-left: 30px;
            opacity: 0.9;
            transition: opacity 0.3s;
        }
        .navbar-links a:hover {
            opacity: 1;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 30px 0;
            color: white;
        }
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 14px;
            opacity: 0.9;
        }
        /* 员工列表样式 */
        .section-title {
            text-align: center;
            padding: 20px;
            color: white;
        }
        .section-title h2 {
            font-size: 24px;
            font-weight: 500;
        }
        .search-box {
            max-width: 500px;
            margin: 0 auto 30px;
            display: flex;
            gap: 10px;
        }
        .search-box input {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 25px;
            font-size: 15px;
        }
        .search-box button {
            padding: 12px 30px;
            background: #4a9b38;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 15px;
        }
        .employee-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 20px 0;
        }
        .employee-card {
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        .employee-card:hover {
            transform: translateY(-5px);
        }
        .employee-photo {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 80px;
            color: #ccc;
            overflow: hidden;
        }
        .employee-photo img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .employee-info {
            padding: 20px;
        }
        .employee-name {
            font-size: 20px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 8px;
        }
        .employee-meta {
            display: flex;
            gap: 15px;
            margin-bottom: 12px;
            font-size: 13px;
            color: #666;
        }
        .employee-skills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
        }
        .skill-tag {
            background: #e8f0fe;
            color: #1E3A8A;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
        }
        .employee-rating {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        .stars {
            color: #f59e0b;
        }
        /* 员工详情样式 */
        .profile-card {
            background: white;
            border-radius: 24px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.3);
            overflow: hidden;
            max-width: 500px;
            margin: 0 auto;
        }
        .profile-header {
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .profile-photo {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            border: 5px solid rgba(255,255,255,0.3);
            background: white;
            margin: 0 auto 20px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 70px;
            color: #ccc;
        }
        .profile-photo img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .profile-name {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .profile-body {
            padding: 30px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }
        .info-item {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        .info-item-value {
            font-size: 24px;
            font-weight: 600;
            color: #1E3A8A;
            margin-bottom: 5px;
        }
        .skills-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 25px;
        }
        .skill-badge {
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }
        .rating-section {
            background: #f8f9fa;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 25px;
        }
        .btn-primary, .btn-secondary {
            flex: 1;
            padding: 15px 30px;
            border-radius: 12px;
            font-size: 16px;
            text-decoration: none;
            text-align: center;
            border: none;
            cursor: pointer;
        }
        .btn-primary {
            background: linear-gradient(135deg, #4a9b38 0%, #3d7a2e 100%);
            color: white;
        }
        .btn-secondary {
            background: white;
            color: #4a9b38;
            border: 2px solid #4a9b38;
        }
        .back-link {
            display: inline-block;
            color: white;
            text-decoration: none;
            margin-bottom: 20px;
        }
        .footer {
            text-align: center;
            padding: 30px 20px;
            color: rgba(255,255,255,0.8);
            font-size: 12px;
        }
        .footer a {
            color: rgba(255,255,255,0.9);
        }
        @media (max-width: 600px) {
            .container { padding: 10px; }
            .header h1 { font-size: 22px; }
            .employee-grid { grid-template-columns: 1fr; }
            .info-grid { grid-template-columns: 1fr; }
            .navbar-links { display: none; }
        }
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar">
        <div class="navbar-content">
            <a href="/" class="navbar-brand">🏠 嘉美净清洁</a>
            <div class="navbar-links">
                <a href="/">首页</a>
                <a href="employee.php">员工风采</a>
                <a href="/#contact">联系我们</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="header">
            <h1>四川嘉美净清洁服务有限公司</h1>
            <p>专业家政服务，让您的生活更美好</p>
        </div>

        <?php if ($is_detail): ?>
            <?php
            $employee = getEmployee($id);
            if ($employee):
            ?>
            <a href="employee.php" class="back-link">← 返回员工列表</a>
            
            <div class="profile-card">
                <div class="profile-header">
                    <div class="profile-photo">
                        <?php if ($employee['photo_path'] && file_exists($employee['photo_path'])): ?>
                        <img src="<?php echo $employee['photo_path']; ?>" alt="<?php echo $employee['name']; ?>">
                        <?php else: ?>
                        👤
                        <?php endif; ?>
                    </div>
                    <div class="profile-name"><?php echo $employee['name']; ?></div>
                    <span style="background: rgba(255,255,255,0.2); padding: 6px 16px; border-radius: 20px;">专业家政服务人员</span>
                </div>
                
                <div class="profile-body">
                    <div class="info-grid">
                        <?php if ($employee['age']): ?>
                        <div class="info-item">
                            <div class="info-item-value"><?php echo $employee['age']; ?></div>
                            <div style="font-size: 12px; color: #666;">年龄</div>
                        </div>
                        <?php endif; ?>
                        
                        <?php if ($employee['work_years']): ?>
                        <div class="info-item">
                            <div class="info-item-value"><?php echo $employee['work_years']; ?></div>
                            <div style="font-size: 12px; color: #666;">工龄(年)</div>
                        </div>
                        <?php endif; ?>
                        
                        <div class="info-item">
                            <div class="info-item-value"><?php echo $employee['review_count']; ?></div>
                            <div style="font-size: 12px; color: #666;">服务次数</div>
                        </div>
                    </div>
                    
                    <?php if ($employee['skills']): ?>
                    <div style="margin-bottom: 25px;">
                        <div style="font-size: 12px; color: #999; margin-bottom: 10px;">专业技能</div>
                        <div class="skills-list">
                            <?php 
                            $skills_array = explode(',', $employee['skills']);
                            foreach ($skills_array as $skill): 
                            ?>
                            <span class="skill-badge"><?php echo trim($skill); ?></span>
                            <?php endforeach; ?>
                        </div>
                    </div>
                    <?php endif; ?>
                    
                    <div class="rating-section">
                        <div style="font-size: 28px; color: #f59e0b; margin-bottom: 10px;">
                            <?php for ($i = 0; $i < 5; $i++): ?>
                                <?php echo $i < floor($employee['rating']) ? '⭐' : '☆'; ?>
                            <?php endfor; ?>
                        </div>
                        <div style="font-size: 36px; font-weight: 700;"><?php echo $employee['rating']; ?></div>
                        <div style="font-size: 14px; color: #666; margin-top: 5px;">基于 <?php echo $employee['review_count']; ?> 条客户评价</div>
                    </div>
                    
                    <div class="action-buttons">
                        <a href="tel:0816-2348822" class="btn-primary">📞 预约服务</a>
                        <a href="employee.php" class="btn-secondary">查看更多员工</a>
                    </div>
                </div>
            </div>
            <?php else: ?>
            <div style="text-align: center; padding: 60px 20px; color: white;">
                <div style="font-size: 120px; font-weight: 700; opacity: 0.3;">404</div>
                <div style="font-size: 24px; margin: 20px 0;">员工不存在</div>
                <a href="employee.php" class="btn-primary" style="display: inline-block; text-decoration: none;">返回员工列表</a>
            </div>
            <?php endif; ?>
            
        <?php else: ?>
            <!-- 员工列表页面 -->
            <div class="section-title">
                <h2>🌟 我们的服务团队</h2>
                <p style="margin-top: 10px; opacity: 0.9;">专业、可靠、值得信赖的家政服务人员</p>
            </div>
            
            <!-- 搜索框 -->
            <form class="search-box" method="get">
                <input type="text" name="search" placeholder="搜索员工姓名或技能..." 
                       value="<?php echo isset($_GET['search']) ? htmlspecialchars($_GET['search']) : ''; ?>">
                <button type="submit">搜索</button>
            </form>
            
            <?php
            $search = isset($_GET['search']) ? $_GET['search'] : '';
            $employees = getEmployees($search);
            ?>
            
            <?php if (count($employees) > 0): ?>
            <div class="employee-grid">
                <?php foreach ($employees as $emp): ?>
                <a href="employee.php?id=<?php echo $emp['id']; ?>" class="employee-card">
                    <div class="employee-photo">
                        <?php if ($emp['photo_path'] && file_exists($emp['photo_path'])): ?>
                        <img src="<?php echo $emp['photo_path']; ?>" alt="<?php echo $emp['name']; ?>">
                        <?php else: ?>
                        👤
                        <?php endif; ?>
                    </div>
                    <div class="employee-info">
                        <div class="employee-name"><?php echo $emp['name']; ?></div>
                        <div class="employee-meta">
                            <?php if ($emp['age']): ?>
                            <span>🎂 <?php echo $emp['age']; ?>岁</span>
                            <?php endif; ?>
                            <?php if ($emp['work_years']): ?>
                            <span>💼 <?php echo $emp['work_years']; ?>年经验</span>
                            <?php endif; ?>
                        </div>
                        <?php if ($emp['skills']): ?>
                        <div class="employee-skills">
                            <?php 
                            $emp_skills = explode(',', $emp['skills']);
                            $emp_skills_slice = array_slice($emp_skills, 0, 3);
                            foreach ($emp_skills_slice as $skill): 
                            ?>
                            <span class="skill-tag"><?php echo trim($skill); ?></span>
                            <?php endforeach; ?>
                        </div>
                        <?php endif; ?>
                        <div class="employee-rating">
                            <span class="stars">⭐ <?php echo $emp['rating']; ?></span>
                            <span style="color: #999;">(<?php echo $emp['review_count']; ?>条评价)</span>
                        </div>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>
            <?php else: ?>
            <div style="text-align: center; padding: 60px 20px; color: white;">
                <div style="font-size: 60px; margin-bottom: 20px; opacity: 0.5;">👥</div>
                <h3>暂无员工信息</h3>
                <p>敬请期待我们优秀的服务团队</p>
            </div>
            <?php endif; ?>
        <?php endif; ?>
        
        <div class="footer">
            <p>联系电话：0816-2348822 | <a href="/">返回公司首页</a></p>
            <p>© 2026 四川嘉美净清洁服务有限公司 版权所有</p>
        </div>
    </div>
</body>
</html>
