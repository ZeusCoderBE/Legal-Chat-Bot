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

function typeMessage($element, message) {
    const words = message.split(" ");
    let index = 0;

    isTyping = true; // Bắt đầu trạng thái gõ
    updateSendButtonState(); // Vô hiệu hóa nút Send khi chatbot đang gõ

    const interval = setInterval(() => {
        if (index < words.length) {
            $element.append(words[index] + " ");
            index++;
            $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));
        } else {
            clearInterval(interval);
            isTyping = false; // Kết thúc trạng thái gõ
            updateSendButtonState(); // Cập nhật trạng thái nút Send sau khi hoàn thành
        }
    }, 150); // Điều chỉnh tốc độ gõ chữ (150ms mỗi từ)
}

function updateSendButtonState() {
    // Chỉ kích hoạt nút Send nếu có ký tự trong input, chatbot không đang gõ và không đang chờ phản hồi
    if ($userInput.val().trim() !== "" && !isTyping && !isLoading) {
        $sendButton.addClass('active').removeClass('disabled').prop('disabled', false);
    } else {
        $sendButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
}

function sendMessage() {
    const query = $userInput.val().trim();
    if (!query || isLoading || isTyping) return; // Không gửi tin nếu đang gõ, input trống, hoặc đang chờ phản hồi

    $sendButton.prop('disabled', true).removeClass('active').addClass('disabled');

    isLoading = true; // Bắt đầu trạng thái chờ phản hồi
    $('#loading-indicator').text("Loading...");

    const $chatOutput = $('#chat-output');
    $chatOutput.append(`
        <div class="chat-message user">
            <div class="avatar user-avatar" style="background-image: url('https://media.istockphoto.com/id/1300845620/vector/user-icon-flat-isolated-on-white-background-user-symbol-vector-illustration.jpg?s=612x612&w=0&k=20&c=yBeyba0hUkh14_jgv1OKqIH0CCSWU_4ckRkAoy2p73o=');"></div>
            <div class="message">${query}</div>
        </div>
    `);

    $userInput.val(''); // Xóa nội dung input sau khi gửi
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

                let formattedAnswer = "";
                if (Array.isArray(data.answer)) {
                    data.answer.forEach((answer, index) => {
                        formattedAnswer += `Answer ${index + 1}: ${answer}\n\n`;
                    });
                } else {
                    formattedAnswer = data.answer;
                }
                formattedAnswer = formattedAnswer.replace(/\n/g, "<br>");
                formattedAnswer = formattedAnswer.replace(/\n\n/g, "<br>");

                const $botMessage = $(`
                    <div class="chat-message bot">
                        <div class="avatar bot-avatar" style="background-image: url('https://png.pngtree.com/png-vector/20230225/ourmid/pngtree-smart-chatbot-cartoon-clipart-png-image_6620453.png');"></div>
                        <div class="message"></div>
                    </div>
                `);
                $chatOutput.append($botMessage);

                // Sử dụng hiệu ứng gõ từng từ
                typeMessage($botMessage.find(".message"), formattedAnswer);

                $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));
                isLoading = false; // Hoàn tất trạng thái chờ phản hồi
                updateSendButtonState(); // Cập nhật trạng thái nút Send sau khi hoàn thành
                $('#loading-indicator').text("");
            }, 800);
        }
    });
}
