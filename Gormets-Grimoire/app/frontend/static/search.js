
$(function() {
$("#searchInput").autocomplete({
	source: function(request, response) {
	$.ajax({
		url: "/search_ingredients",  // endpoint returning JSON data for autocomplete
		dataType: "json",
		data: { 
			term: request.term 
			},
		success: function(data) {
		response($.map(data, function(item) {
			return { label: item, value: item };
		}));
		},
		error: function() {
		response([]);
		}
	});
	},
	minLength: 2,
	select: function(event, ui) {
	//redirect to search_results.html with the selected ingredient
	if (ui.item) 
	{
		window.location.href = `/search_results?ingredient=${encodeURIComponent(ui.item.value)}`;
	}
	}
});
});
