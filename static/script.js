function toggleSidebar() {
    const $sidebar = $('.sidebar');
    const $sidebarContent = $('.sidebar-content');
    const $toggleButton = $('.toggle-button');
    const $header = $('.header');

    if ($sidebar.width() === 250) {
        // Thu nhỏ sidebar
        $sidebar.css('width', '0');
        $sidebarContent.hide();
        $toggleButton.attr('title', 'Open sidebar');

        // Di chuyển toggle-button vào header khi sidebar đóng
        $header.append($toggleButton);
    } else {
        // Phóng to sidebar
        $sidebar.css('width', '250px');
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

$('#send-button').on('click', sendMessage);

$('#user-query').on('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

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
    }, 50); // Điều chỉnh tốc độ gõ chữ (50ms mỗi từ)
}

function updateSendButtonState() {
    // Chỉ kích hoạt nút Send nếu có ký tự trong input, chatbot không đang gõ và không đang chờ phản hồi
    if ($userInput.val().trim() !== "" && !isTyping && !isLoading) {
        $sendButton.addClass('active').removeClass('disabled').prop('disabled', false);
    } else {
        $sendButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
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
        // Giới hạn nội dung hiển thị (ví dụ: 100 ký tự đầu tiên)
        const shortContent = doc.length > 100 ? doc.substring(0, 100) + '...' : doc;

        // Tạo thẻ cho document
        const docElement = $(`
            <div class="relevant-document" data-full-content="${doc}">
                ${shortContent}
            </div>
        `);

        // Thêm sự kiện click để mở rộng nội dung đầy đủ
        docElement.on('click', function() {
            const fullContent = $(this).data('full-content');
            openFullscreenDocument(fullContent);
        });

        documentsWrapper.append(docElement);
    });
}

// Hàm mở nội dung đầy đủ trong modal
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

// Gọi hàm displayRelevantDocuments khi có dữ liệu từ chatbot
function processResponse(data) {
    const { answer, lst_Relevant_Documents } = data;
    let formattedAnswer = "";

    // Chuẩn bị nội dung phản hồi của chatbot với xuống dòng bằng <br>
    if (Array.isArray(answer)) {
        answer.forEach((ans, index) => {
            formattedAnswer += `Answer ${index + 1}: ${ans.replace(/\n/g, "<br>")}<br><br>`;
        });
    } else {
        formattedAnswer = answer.replace(/\n/g, "<br>");
    }

    // Tạo một phần tử trống để từng từ sẽ được gõ vào đó
    const $chatOutput = $('#chat-output');
    const $botMessage = $(`
        <div class="chat-message bot">
            <div class="avatar bot-avatar" style="background-image: url('https://png.pngtree.com/png-vector/20230225/ourmid/pngtree-smart-chatbot-cartoon-clipart-png-image_6620453.png');"></div>
            <div class="message"></div>
        </div>
    `);
    $chatOutput.append($botMessage);

    // Gọi typeMessage với callback để hiển thị tài liệu liên quan sau khi in xong câu trả lời
    typeMessage($botMessage.find(".message"), formattedAnswer, () => {
        // Gọi hàm để hiển thị các thẻ từ lst_Relevant_Documents
        displayRelevantDocuments(lst_Relevant_Documents);
    });
}

// Điều chỉnh hàm sendMessage để sử dụng processResponse
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

    $userInput.val('');
    $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));

    const $typingIndicator = $(`
        <div class="chat-message bot typing-indicator">
            <div class="avatar bot-avatar" style="background-image: url('https://png.pngtree.com/png-vector/20230225/ourmid/pngtree-smart-chatbot-cartoon-clipart-png-image_6620453.png');"></div>
            <div class="message"><span>.</span><span>.</span><span>.</span></div>
        </div>
    `);
    $chatOutput.append($typingIndicator);
    $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));

    $.ajax({
        url: 'http://127.0.0.1:5000/chatbot',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ query: query }),
        success: function(data) {
            setTimeout(() => {
                $typingIndicator.remove();
                processResponse(data); // Sử dụng processResponse để xử lý phản hồi
                $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));
                isLoading = false;
                updateSendButtonState();
                $('#loading-indicator').text("");
            }, 800);
        }
    });
}