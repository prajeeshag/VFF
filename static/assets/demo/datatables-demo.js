// Call the dataTables jQuery plugin
$(document).ready(function() {
	$('#dataTable').DataTable({
		"autoWidth": true,
	});
});

$(document).ready(function() {
    $('#dataTableActivity').DataTable({
        "order": [[ 0, 'desc' ]],
				"autoWidth": true
    });
});
