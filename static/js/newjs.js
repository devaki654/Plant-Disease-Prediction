$(document).ready(function() {
    $('form').on('submit', function(event) {
        event.preventDefault();
        var formData = new FormData($(this)[0]);

        $.ajax({
            type: 'POST',
            url: '/predict',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                var predictedLabel = response.predicted_label;
                $('#result').html('Result: ' + predictedLabel);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});
