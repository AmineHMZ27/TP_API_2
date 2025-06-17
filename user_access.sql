CREATE TABLE user_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    stream_name VARCHAR(100) NOT NULL,
    access_level ENUM('read', 'write', 'admin') DEFAULT 'read',
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
