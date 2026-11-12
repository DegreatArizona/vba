$(document).ready(function(){
  $("#searchInput").on("keyup", function() {
    var value = $(this).val().toLowerCase();
    $("#tableBody tr").filter(function() {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
  });
});

function filterTableByStatus(status) {
const rows = document.querySelectorAll("#tableBody tr");

rows.forEach(row => {
const statusCell = row.querySelector("td:nth-child(5) span");
if (status === "" || statusCell.textContent === status) {
  row.style.display = ""; 
} else {
  row.style.display = "none"; 
}
});
}