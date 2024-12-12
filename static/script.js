// Hàm thao tác với sidebar
function toggleSidebar() {
    const $sidebar = $('.sidebar');
    const $sidebarContent = $('.sidebar-content');
    const $toggleButton = $('.toggle-button');
    const $header = $('.header');

    if ($sidebar.width() === 300) {
        // Thu nhỏ sidebar
        $sidebar.css('width', '0');
        $sidebarContent.hide();
        $toggleButton.attr('title', 'Open sidebar');

        // Di chuyển toggle-button vào header khi sidebar đóng
        $header.append($toggleButton);
    } else {
        // Phóng to sidebar
        $sidebar.css('width', '300px');
        $sidebarContent.show();
        $toggleButton.attr('title', 'Close sidebar');

        // Di chuyển toggle-button vào sidebar khi mở
        $sidebar.append($toggleButton);
    }
}

const $userInput = $('#user-query');
const $sendButton = $('#send-button');
let isLoading = false; // Trạng thái khi chatbot đang xử lý phản hồi
let isTyping = false;  // Trạng thái khi chatbot đang in từng từ của câu trả lời

// Kiểm tra nội dung của input-area để bật/tắt nút Send
$userInput.on('input', function() {
    updateSendButtonState(); // Cập nhật trạng thái nút Send khi người dùng nhập liệu
});

function updateSendButtonState() {
    // Chỉ kích hoạt nút Send nếu có ký tự trong input, chatbot không đang gõ và không đang chờ phản hồi
    if ($userInput.val().trim() !== "" && !isTyping && !isLoading) {
        $sendButton.addClass('active').removeClass('disabled').prop('disabled', false);
    } else {
        $sendButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
}

// Logic event khi user click button Send
$('#send-button').on('click', sendMessage);

// Logic event khi user ấn nút Enter thay thì button Send
$('#user-query').on('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

// Hàm lấy URL dựa trên mô hình hiện tại
function getModelUrl() {
    const currentModel = $(".model-name").text().trim();

    if (currentModel === 'T5 Summary') {
        return 'http://127.0.0.1:5000/chatbot-with-T5Sum';
    } else if (currentModel === 'Gemini') {
        return 'http://127.0.0.1:5000/chatbot-with-gemini';
    } else {
        return 'http://127.0.0.1:5000/chatbot-with-T5Sum'; // Mặc định
    }
}

// Hàm gửi tin nhắn từ user
function sendMessage() {
    const query = $userInput.val().trim();
    if (!query || isLoading || isTyping) return;

    // Xóa nội dung của relevant-documents-container
    $('#relevant-documents-container').empty();

    $sendButton.prop('disabled', true).removeClass('active').addClass('disabled');
    isLoading = true;
    $('#loading-indicator').text("Loading...");

    const $chatOutput = $('#chat-output');
    $chatOutput.append(`
        <div class="chat-message user">
            <div class="avatar user-avatar" style="background-image: url('https://media.istockphoto.com/id/1300845620/vector/user-icon-flat-isolated-on-white-background-user-symbol-vector-illustration.jpg?s=612x612&w=0&k=20&c=yBeyba0hUkh14_jgv1OKqIH0CCSWU_4ckRkAoy2p73o=');"></div>
            <div class="message">${query}</div>
        </div>
    `);

    // Lưu tin nhắn của người dùng vào database
    saveMessage(currentSessionId, 'user', query);

    // Kiểm tra và thêm phiên chat vào sidebar nếu là tin nhắn đầu tiên
    if ($('#chat-sessions .chat-session[data-session-id="' + currentSessionId + '"]').length === 0) {
        addChatSessionToSidebar(currentSessionId, query);
    }

    $userInput.val('');
    $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));

    const $typingIndicator = $(`
        <div class="chat-message bot typing-indicator">
            <div class="avatar bot-avatar" style="background-image: url('https://png.pngtree.com/png-vector/20230225/ourmid/pngtree-smart-chatbot-cartoon-clipart-png-image_6620453.png');"></div>
            <div class="message" style="font-size: 14px;
                                color: rgba(0, 0, 0, 0.6); 
                                display: flex;
                                align-items: center;">
                Đang suy nghĩ câu trả lời 
                <div class="time-count" style="margin-left: 5px; margin-right: 5px;">
                00:00</div>
                <span>.</span><span>.</span><span>.</span>
            </div>
        </div>
    `);
    $chatOutput.append($typingIndicator);
    $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));

    // Khởi tạo thời gian bắt đầu
    const startTime = Date.now();

    // Cập nhật số phút và giây trong "Đang suy nghĩ câu trả lời"
    const updateTimeInterval = setInterval(() => {
        const elapsedTime = Math.floor((Date.now() - startTime) / 1000); // Tính số giây đã trôi qua
        const minutes = Math.floor(elapsedTime / 60); // Tính phút
        const seconds = elapsedTime % 60; // Tính giây còn lại

        // Đảm bảo rằng phút và giây đều có 2 chữ số
        const formattedTime = `${minutes < 10 ? '0' : ''}${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        // Cập nhật hiển thị thời gian
        $typingIndicator.find('.time-count').text(formattedTime);
    }, 1000); // Cập nhật mỗi giây

    // Lấy URL của mô hình hiện tại
    const url_Model = getModelUrl();

    $.ajax({
        url: url_Model,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ query: query }),
        success: function(data) {
            setTimeout(() => {
                clearInterval(updateTimeInterval); // Dừng cập nhật thời gian khi có phản hồi
                $typingIndicator.remove();
                processResponse(data); // Sử dụng processResponse để xử lý phản hồi

                // Lưu tin nhắn của chatbot vào database
                saveMessage(currentSessionId, 'bot', data.answer);

                $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));
                isLoading = false;
                updateSendButtonState();
                $('#loading-indicator').text("");
            }, 800);
        }
    });
}

// Hàm xử lý dữ liệu để chatbot phản hồi và lấy ra trích dẫn
function processResponse(data) {
    const { answer, lst_Relevant_Documents } = data;
    let formattedAnswer = "";

    // Vì `answer` bây giờ là một chuỗi, chỉ cần thay thế ký tự xuống dòng bằng <br> để hiển thị đúng
    formattedAnswer = answer.replace(/\n/g, "<br>");
    formattedAnswer = formattedAnswer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Tạo một phần tử trống để từng từ sẽ được gõ vào đó
    const $chatOutput = $('#chat-output');
    const $botMessage = $(`
        <div class="chat-message bot">
            <div class="avatar bot-avatar" style="background-image: url('https://png.pngtree.com/png-vector/20230225/ourmid/pngtree-smart-chatbot-cartoon-clipart-png-image_6620453.png');"></div>
            <div class="message"></div>
        </div>
    `);
    $chatOutput.append($botMessage);

    // Gọi typeMessage để hiển thị từng từ của câu trả lời
    typeMessage($botMessage.find(".message"), formattedAnswer, () => {
        // Sau khi hoàn thành việc hiển thị câu trả lời, gọi hàm hiển thị tài liệu liên quan
        displayRelevantDocuments(lst_Relevant_Documents);
    });
}

// Hàm cho chatbot in ra phản hồi cho user
function typeMessage($element, message, callback) {
    const words = message.split(" ");
    let index = 0;

    isTyping = true; // Bắt đầu trạng thái gõ
    updateSendButtonState(); // Vô hiệu hóa nút Send khi chatbot đang gõ

    const interval = setInterval(() => {
        if (index < words.length) {
            $element.append(words[index] + " ");
            index++;
            $element.parent().scrollTop($element.parent().prop('scrollHeight'));
        } else {
            clearInterval(interval);
            isTyping = false; // Kết thúc trạng thái gõ
            updateSendButtonState(); // Cập nhật trạng thái nút Send sau khi hoàn thành
            if (callback) callback(); // Gọi callback sau khi in xong
        }
    }, 25); // Điều chỉnh tốc độ gõ chữ (25ms mỗi từ)
}

// Hàm tạo thẻ cho lst_Relevant_Documents
function displayRelevantDocuments(documents) {
    const container = $('#relevant-documents-container');
    container.empty(); // Xóa các thẻ cũ nếu có

    // Tạo div chứa tiêu đề
    const title = $('<div class="references-title">Trích dẫn tham khảo</div>');
    container.append(title);

    // Tạo một div riêng cho các thẻ tài liệu
    const documentsWrapper = $('<div class="documents-wrapper"></div>');
    container.append(documentsWrapper);

    documents.forEach((doc, index) => {
        // // Giới hạn nội dung hiển thị (ví dụ: 100 ký tự đầu tiên)
        // const shortContent = doc.length > 100 ? doc.substring(0, 100) + '...' : doc;

        // // Tạo thẻ cho document
        // const docElement = $(`
        //     <div class="relevant-document" data-full-content="${doc}">
        //         ${shortContent}
        //     </div>
        // `);

        // Lấy phần metadata từ chuỗi trích dẫn tài liệu
        const parts = doc.split('<=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>');

        // Kiểm tra nếu có ít nhất hai phần (metadata và nội dung)
        if (parts.length > 1) {
            const contentPart = parts[0].trim(); // Metadata phần đầu tiên
            const metadataPart = parts[1].trim();  // Nội dung tài liệu phần thứ hai

            // Trích xuất thông tin từ metadata, ví dụ: 'loai_van_ban' và 'so_hieu'
            const loaiVanBanMatch = metadataPart.match(/Loại văn bản: (.*)/);
            const soHieuMatch = metadataPart.match(/Số hiệu: (.*)/);

            // Lấy thông tin từ các nhóm đã trích xuất
            const loaiVanBan = loaiVanBanMatch ? loaiVanBanMatch[1] : "N/A";
            const soHieu = soHieuMatch ? soHieuMatch[1] : "N/A";

            // Giới hạn nội dung hiển thị (ví dụ: 20 ký tự đầu tiên)
            const shortContent = contentPart.length > 20 ? contentPart.substring(0, 20) + '...' : contentPart;

            // Tạo nội dung thẻ tài liệu mới
            const docElement = $(`
                <div class="relevant-document" data-full-content="${doc}">
                    ${loaiVanBan} ${soHieu}
                    <hr class="custom-hr">
                    ${shortContent}
                </div>
            `);

            // Thêm sự kiện click để mở rộng nội dung đầy đủ
            docElement.on('click', function() {
                const fullContent = $(this).data('full-content');
                openFullscreenDocument(fullContent);
            });

            documentsWrapper.append(docElement);
        }
    });
}

// Hàm mở nội dung đầy đủ khi click vào Trích dẫn
function openFullscreenDocument(content) {
    // Thay thế ký tự xuống dòng bằng thẻ <br> để hiển thị cách dòng đúng
    const formattedContent = content.replace(/\n/g, "<br>");

    // Tạo overlay để hiển thị nội dung phóng to
    const overlay = $(`
        <div class="fullscreen-overlay">
            <div class="fullscreen-document">
                <div class="document-content">${formattedContent}</div>
            </div>
        </div>
    `);

    // Thêm sự kiện click vào overlay để đóng khi nhấp ra bên ngoài tài liệu
    overlay.on('click', function(e) {
        if ($(e.target).is('.fullscreen-overlay')) {
            overlay.remove(); // Đóng overlay khi click vào vùng tối
        }
    });

    // Thêm overlay vào body
    $('body').append(overlay);
}

// Biến lưu session ID hiện tại
let currentSessionId = null;

// Hàm khởi tạo session mới
function startNewSession() {
    $.ajax({
        url: 'http://127.0.0.1:5000/start-session',
        type: 'POST',
        success: function (response) {
            currentSessionId = response.session_id; // Lưu session ID
            localStorage.setItem('session_id', currentSessionId); // Lưu vào localStorage
            console.log("New session started with ID:", currentSessionId);

            // Xóa khung chat và hiển thị tin nhắn mặc định
            $('#chat-output').empty();
            $('#relevant-documents-container').empty();
            const defaultMessage = `
                <div class="chat-message bot">
                    <div class="avatar bot-avatar" style="background-image: url('https://png.pngtree.com/png-vector/20230225/ourmid/pngtree-smart-chatbot-cartoon-clipart-png-image_6620453.png');"></div>
                    <div class="message">Xin chào Bạn, Tôi là một trợ lý chuyên hỗ trợ về pháp luật Việt Nam. Bạn có câu hỏi gì xin đừng ngần ngại hỏi Tôi nhé!</div>
                </div>
            `;
            $('#chat-output').append(defaultMessage);
        },
        error: function () {
            alert("Error: Unable to start new session.");
        }
    });
}

// Hàm xử lý khi user click New Chat
$('#new-chat').on('click', function (event) {
    event.preventDefault();
    if (confirm("Bạn có chắc chắn muốn bắt đầu một phiên trò chuyện mới?")) {
        localStorage.removeItem('session_id'); // Xóa session ID cũ
        startNewSession(); // Tạo session mới

        const $inputArea = $('#user-query');  // Sử dụng id 'user-query' thay vì class 'input-area'
        // Vô hiệu hóa input và thay đổi placeholder
        $inputArea.prop('disabled', false);  // Vô hiệu hóa input
        $inputArea.attr('placeholder', 'Nhập tin nhắn ...');  // Thay đổi placeholder

        loadChatSessions(); // Cập nhật lại danh sách phiên chat

        // Vô hiệu hóa Clear Chat khi bắt đầu một chat mới
        $clearChatButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
});

// Hàm lưu tin nhắn vào database
function saveMessage(sessionId, sender, message) {
    $.ajax({
        url: 'http://127.0.0.1:5000/save-message',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            session_id: sessionId,
            sender: sender,
            message: message
        }),
        success: function(response) {
            console.log("Message saved:", response);
        },
        error: function() {
            console.error("Error saving message.");
        }
    });
}

// Hàm load danh sách các phiên chat cũ
function loadChatSessions() {
    $.ajax({
        url: 'http://127.0.0.1:5000/get-sessions',
        type: 'GET',
        success: function(response) {
            const sessions = response.sessions;
            const $chatSessions = $('#chat-sessions');
            $chatSessions.empty(); // Xóa nội dung cũ

            sessions.forEach(session => {
                const firstMessage = session.first_message || "No message yet";
                const truncatedMessage = firstMessage.length > 30 
                    ? firstMessage.substring(0, 30) + "..." 
                    : firstMessage;

                const sessionElement = $(`
                    <div class="chat-session" data-session-id="${session.id}">
                        <div class="chat-session-content">${truncatedMessage}</div>
                    </div>
                `);

                // Gắn sự kiện click để load lịch sử chat
                sessionElement.on('click', function() {
                    loadChatHistory(session.id);
                });

                $chatSessions.append(sessionElement);
            });
        },
        error: function() {
            console.error("Error fetching chat sessions");
        }
    });
}

// Logic event khi load lại web thì sẽ load danh sách các phiên chat cũ
$(document).ready(function() {
    // Tải danh sách các phiên chat
    loadChatSessions();

    // Đảm bảo rằng phần tử model-name luôn hiển thị "T5 Summary" khi trang được tải
    $(".model-name").text("T5Sum");

    // Gắn sự kiện click vào phần tử #change-model
    $("#change-model").on("click", function() {
        toggleModel();  // Gọi hàm toggleModel khi click
    });

    const $inputArea = $('#user-query');  // Sử dụng id 'user-query' thay vì class 'input-area'
    // Vô hiệu hóa input và thay đổi placeholder
    $inputArea.prop('disabled', true);  // Vô hiệu hóa input
    $inputArea.attr('placeholder', 'Click "Đoạn Chat Mới" để bắt đầu một phiên trò chuyện mới!');  // Thay đổi placeholder
});

// Hàm thay đổi mô hình và cập nhật href
function toggleModel() {
    const currentModel = $(".model-name").text().trim();

    if (currentModel === 'T5Sum') {
        $(".model-name").text('Gemini');
        $(".model-name").addClass("gemini-model");
    } else {
        $(".model-name").text('T5Sum');
        $(".model-name").removeClass("gemini-model");
    }
}

// Hàm cập nhật trạng thái của nút Clear Chat
function updateClearChatButtonState() {
    // Kiểm tra nếu có tin nhắn từ người dùng trong chat-output
    const userMessagesExist = $chatOutput.find('.chat-message.user').length > 0;
    
    // Nếu có tin nhắn từ người dùng, bật nút Clear Chat
    if (userMessagesExist) {
        $clearChatButton.removeClass('disabled').addClass('active').prop('disabled', false);
    } else {
        $clearChatButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
}

// Lắng nghe sự kiện click vào một phiên chat từ sidebar
$('.chat-session').on('click', function() {
    // Khi người dùng click vào phiên chat, bật nút Clear Chat nếu có tin nhắn
    updateClearChatButtonState();
});

// Hàm load lại lịch sử chat của một phiên
function loadChatHistory(sessionId) {
    console.log("Loading chat history for session ID:", sessionId);

    // Gọi API để lấy lịch sử chat
    $.ajax({
        url: `http://127.0.0.1:5000/get-chat-history/${sessionId}`,
        type: 'GET',
        success: function (response) {
            const chatHistory = response.chat_history;
            const $chatOutput = $('#chat-output');
            $chatOutput.empty(); // Xóa khung chat hiện tại

            // Duyệt qua lịch sử chat và hiển thị từng tin nhắn
            chatHistory.forEach(chat => {
                const isBot = chat.sender === 'bot';
                
                // Chuyển các đoạn có dấu ** thành thẻ <strong> để in đậm
                let formattedMessage = chat.message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

                // Thay thế \n bằng <br> để hiển thị xuống dòng
                formattedMessage = formattedMessage.replace(/\n/g, "<br>");

                const messageHtml = `
                    <div class="chat-message ${isBot ? 'bot' : 'user'}">
                        <div class="avatar ${isBot ? 'bot-avatar' : 'user-avatar'}" 
                             style="background-image: url('${isBot ? 'https://png.pngtree.com/png-vector/20230225/ourmid/pngtree-smart-chatbot-cartoon-clipart-png-image_6620453.png' : 'https://media.istockphoto.com/id/1300845620/vector/user-icon-flat-isolated-on-white-background-user-symbol-vector-illustration.jpg?s=612x612&w=0&k=20&c=yBeyba0hUkh14_jgv1OKqIH0CCSWU_4ckRkAoy2p73o='}');">
                        </div>
                        <div class="message">${formattedMessage}</div>
                    </div>
                `;
                $chatOutput.append(messageHtml);
            });

            const $inputArea = $('#user-query');  // Sử dụng id 'user-query' thay vì class 'input-area'
            // Vô hiệu hóa input và thay đổi placeholder
            $inputArea.prop('disabled', false);  // Mở input
            $inputArea.attr('placeholder', 'Nhập tin nhắn ...');  // Thay đổi placeholder

            // Sau khi tải xong lịch sử chat, cập nhật trạng thái nút Clear Chat
            updateClearChatButtonState();

            // Cập nhật session ID hiện tại
            currentSessionId = sessionId;
            localStorage.setItem('session_id', sessionId); // Lưu lại session ID
        },
        error: function () {
            console.error("Error loading chat history.");
        }
    });
}

// Hàm add phiên chat hiện tại vào sidebar ngay sau khi user gửi tin nhắn
function addChatSessionToSidebar(sessionId, firstMessage) {
    const $chatSessions = $('#chat-sessions');
    const truncatedMessage = firstMessage.length > 30 
        ? firstMessage.substring(0, 30) + "..." 
        : firstMessage;

    const sessionElement = $(`
        <div class="chat-session" data-session-id="${sessionId}">
            <div class="chat-session-content">${truncatedMessage}</div>
        </div>
    `);

    // Gắn sự kiện click vào phiên chat mới
    sessionElement.on('click', function() {
        loadChatHistory(sessionId);
    });

    // Thêm phiên chat mới vào đầu danh sách
    $chatSessions.prepend(sessionElement);
}

// Lấy đối tượng của nút Clear Chat và chat-output
const $clearChatButton = $('#clear-chat');
const $chatOutput = $('#chat-output');

// Lắng nghe sự kiện click vào nút Clear Chat
$clearChatButton.on('click', function() {
    if (confirm("Bạn có chắc chắn muốn xóa phiên Chat này?")) {
        // Xóa chat ở frontend
        clearChatHistory();

        const $inputArea = $('#user-query');  // Sử dụng id 'user-query' thay vì class 'input-area'
        // Vô hiệu hóa input và thay đổi placeholder
        $inputArea.prop('disabled', true);  // Vô hiệu hóa input
        $inputArea.attr('placeholder', 'Click "Đoạn Chat Mới" để bắt đầu một phiên trò chuyện mới!');  // Thay đổi placeholder

        // Gửi yêu cầu đến backend để xóa chat
        deleteChatSession(currentSessionId);
    }
});

// Hàm xóa toàn bộ lịch sử chat trong giao diện
function clearChatHistory() {
    $chatOutput.empty();
    $('#relevant-documents-container').empty();
    updateClearChatButtonState(); // Cập nhật lại trạng thái của nút Clear Chat
}

// Hàm gửi yêu cầu xóa chat tới backend
function deleteChatSession(sessionId) {
    $.ajax({
        url: `http://127.0.0.1:5000/delete-session/${sessionId}`,
        type: 'DELETE',
        success: function(response) {
            console.log('Session deleted successfully');
            // Cập nhật lại danh sách các phiên chat trong sidebar
            loadChatSessions();
        },
        error: function() {
            console.error("Error deleting session.");
        }
    });
}

