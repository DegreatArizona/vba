$(document).ready(function() {

    // Toggle chatbox visibility

    $('#chat-toggle').click(function() {

        $('#chatbox').toggle();

    });



    // Close the chatbox

    $('#chat-close').click(function() {
        $('#chatbox').hide();
    });

    // Send message on button click

    $('#send-message').click(function() {
        // Get CSRF token from cookies
        var csrftoken = Cookies.get('csrftoken');

        // Set CSRF token in AJAX headers
        $.ajaxSetup({

            headers: { 'X-CSRFToken': csrftoken }

        });
        // Get the prompt text

        var prompt = $('#prompt').val();

        var dateTime = new Date();

        var time = dateTime.toLocaleTimeString();



        // Display the prompt in the chat window

        $('#chat-response').append('<p>(' + time + ') <i class="bi bi-person"></i>: ' + prompt + '</p>');

        $('#prompt').val(''); // Clear the input



        // Show bot typing indicator

        var typingIndicator = $('<p id="typing-indicator"><i class="bi bi-robot"></i>: Bot is typing...</p>');

        $('#chat-response').append(typingIndicator);



        // Send prompt to the backend

        $.ajax({

            url: '/chatbot/',  // Ensure this matches your Django URL configuration

            type: 'POST',

            data: {prompt: prompt},

            dataType: 'json',

            success: function(data) {

                // Remove the typing indicator

                $('#typing-indicator').remove();

                

                // Display response from backend

                $('#chat-response').append('<p>(' + time + ') <i class="bi bi-robot"></i>: ' + data.response + '</p>');

            },

            error: function() {

                // Remove the typing indicator and show an error

                $('#typing-indicator').remove();

                $('#chat-response').append('<p style="color: red;">Error: Could not get a response.</p>');

            }

        });

    });

});