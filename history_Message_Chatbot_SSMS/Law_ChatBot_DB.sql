-- Tạo database
CREATE DATABASE Law_ChatBot_DB;
GO

-- Sử dụng database vừa tạo
USE Law_ChatBot_DB;
GO

-- Tạo bảng Chat_Sessions
CREATE TABLE Chat_Sessions (
    id INT PRIMARY KEY IDENTITY(1,1),  -- ID tự tăng
    create_at DATETIME DEFAULT GETDATE()  -- Ngày giờ tạo phiên
);
GO

-- Tạo bảng Chat_Messages
CREATE TABLE Chat_Messages (
    id INT PRIMARY KEY IDENTITY(1,1),  -- ID tự tăng
    session_id INT,  -- Liên kết đến Chat_Sessions
    sender NVARCHAR(50),  -- Người gửi ("user" hoặc "bot")
    message NVARCHAR(MAX),  -- Nội dung tin nhắn
    send_at DATETIME DEFAULT GETDATE(),  -- Thời gian gửi tin nhắn
    CONSTRAINT FK_ChatSession FOREIGN KEY (session_id) REFERENCES Chat_Sessions(id) ON DELETE CASCADE
);
GO

--select *from chat_sessions
--select *from Chat_Messages

--delete from Chat_Sessions
--delete from Chat_Messages

--DELETE FROM Chat_Sessions WHERE NOT EXISTS (
--    SELECT 1
--    FROM Chat_Messages
--    WHERE Chat_Messages.session_id = Chat_Sessions.id
--);
