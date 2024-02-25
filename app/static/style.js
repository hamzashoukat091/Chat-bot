$(document).ready(function() {
        function scrollToBottom() {
            var chatbox = document.getElementById("chatbox");
            chatbox.scrollTop = chatbox.scrollHeight;
        }
        function getBotResponse() {
            var rawText = $('#textInput').val().trim();
            if (rawText === "") {
                return; // Do nothing if input is empty
            }
            var userHtml = '<p class="userText"><span>' + rawText + '</span></p>';
            $('#textInput').val("");
            $('#chatbox').append(userHtml);
            scrollToBottom();

            document.getElementById('userInput').scrollIntoView({block: 'start', behavior: 'smooth'});
            $.get("/getChatBotResponse", { msg: rawText }).done(function(data) {
                console.log('data', JSON.stringify(data));
                var botHtml = '<p class="botText"><span>' + data.answer + '</span></p>';
                $("#chatbox").append(botHtml);
                document.getElementById('userInput').scrollIntoView({block: 'start', behavior: 'smooth'});
            });
        }

        $('#textInput').keypress(function(e) {
            if(e.which == 13) {
                getBotResponse();
            }
        });
        $('#buttonInput').click(function() {
            getBotResponse();
        });

        // Clear chat button functionality
        $('#clearChatBtn').click(function() {
            $('#chatbox').empty(); // Clear chatbox content
        });
    });
