// script.js

document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');

    searchForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const queryText = document.getElementById('query_text').value;

        // Send the query to the server and handle the response (e.g., display results).
        // You can use JavaScript fetch or AJAX to make a POST request to your Flask server.
    });
});
