function saveUserId(userId) {
  localStorage.setItem('SimpleWebService@userId', userId);
}

function getSelectedMessage() {
  $.ajax({
    url: '{% url "dashboard" %}',
    success: function(data) {
        $('#dados').html(data.html);
    }
});
}