
function labelfor(el){
	var label = $("label[for='" + $(el).attr('id') + "']");
	return label;
};

$(window).on('load', function() { 

	var NU19S = parseInt($('input[name=NU19S]').val());
	var NU21S = parseInt($('input[name=NU21S]').val());

	$('input.disabled').attr('disabled',true)
	$('input.disabled').closest('div').css({"border-style":"solid", "border-color":"red"})
	$('input[name="player_in" ][type="radio"]').attr('disabled',true)
	$('button[name="save"]').attr('disabled',true)
	$('button[name="substitute"]').attr('disabled',true)
	
	$('input[name=player_out][type=radio]').change(function() {

		side = $(this).attr('side')
		var nU19 = 0 
		var nU21 = 0 

		$('input[name=player_out][type=radio][side='+side+']').each(function() {
			el = $(this)
			age = el.data('player-age')
			if (age <= 19) { nU19 += 1 } 
			if (age <= 21) { nU21 += 1 }
		});

		$('input[name=player_out][type=hidden][side='+side+']').each(function() {
			el = $(this)
			age = el.data('player-age')
			if (age <= 19) { nU19 -= 1 } 
			if (age <= 21) { nU21 -= 1 }
		});

		$('input[name=player_in][type=hidden][side='+side+']').each(function() {
			el = $(this)
			age = el.data('player-age')
			if (age <= 19) { nU19 += 1 } 
			if (age <= 21) { nU21 += 1 }
		});

		$("input[name=player_out][type=radio][side="+side+"]").closest('div').css({"border-style":""})

		$(this).closest('div').css({"border-style":"solid", "border-color":"green"})
		age = $(this).data('player-age')

		$('input[name=player_in][type=radio][side='+side+']').each(function() {
			$(this).closest('div').css({"border-style":""})
			$(this).attr('disabled',false)
			$(this).prop('checked', false);
		});

		if (age<=19 && nU19-1 < NU19S){
			$('input[name=player_in][type=radio][side='+side+']').each(function() {
				el = $(this)
				age = el.data('player-age')
				if (age > 19) {
					$(this).closest('div').css({"border-style":"solid", "border-color":"red"})
					$(this).attr('disabled',true)
				}
			});
		}
		else if (age<=21 && nU21-1 < NU21S) {
			$('input[name=player_in][type=radio][side='+side+']').each(function() {
				el = $(this)
				age = el.data('player-age')
				if (age > 21) {
					$(this).closest('div').css({"border-style":"solid", "border-color":"red"})
					$(this).attr('disabled',true)
				}
			});
		}

		$('input.disabled').attr('disabled',true)
		$('input.disabled').closest('div').css({"border-style":"solid", "border-color":"red"})
		$('button[name="save"][side='+side+']').attr('disabled',true)
		$('button[name="substitute"][side='+side+']').attr('disabled',true)
	});

	$('input[name=player_in][type=radio]').change(function() {
		side = $(this).attr('side')
		$('input[name=player_in][type=radio][side='+side+']').filter("input:enabled").closest('div').css({"border-style":""})
		$(this).closest('div').css({"border-style":"solid", "border-color":"green"})
		if ($('input[name=player_out]:checked').val() && $('input[name=player_in]:checked').val()) {
			$('button[name="save"][side='+side+']').attr('disabled',false)
			$('button[name="substitute"][side='+side+']').attr('disabled',false)
		};
	});
});

