// Call the dataTables jQuery plugin
$(document).ready(function() {
	$('#dataTable').DataTable({
		"autoWidth": true,
	});
});

$(document).ready(function() {
    $('#dataTableActivity').DataTable({
				"autoWidth": true
    });
});

$(document).ready(function() {
	$('#fixtureTable').DataTable({
		"paging": false,
		"ordering": false,
		"order":[],
		"pageLength": 100,
		"lengthMenu": [ 100,  ]
	});
});
