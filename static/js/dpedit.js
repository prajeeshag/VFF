
$(document).ready( function() {
	$(".dpedit input[type=file]").css({ 
		"position": "fixed", 
		"right": "100%",
		"bottom": "100%"
	});

	$(".dpedit input[type=file]").each( function() { 
		$(this).change(function(ev) {
			$(".dpedit input[name$='-checked']").val("False")
			$(this).closest('form').submit()
		});
	});

	$(".dpeditSubmitButton").click( function(event) {
		$(".dpedit input[name$='-checked']").val("True")
		event.preventDefault();
		$(this).closest('form').submit()
	});

});


$(window).on("load", function() {
	const ratio = 1.;

	$(".dpedit").each( function () {
		img = $(this).find("img")[0]
		var jcp = Jcrop.attach(img, {aspectRatio:ratio});
		xp1 = $(this).children("input[name$=xp1]").val();
		yp1 = $(this).children("input[name$=yp1]").val();
		xp2 = $(this).children("input[name$=xp2]").val();
		yp2 = $(this).children("input[name$=yp2]").val();
		w = img.width; h = img.height;
		w = img.naturalWidth; h = img.naturalHeight;
		x1 = w*xp1; x2 = w*xp2
		y1 = h*yp1; y2 = h*yp2
		w1 = x2-x1; h1 = y2-y1
		wh = Math.min(w1,h1)
		const rect = Jcrop.Rect.create(x1,y1,wh,wh);
		jcp.newWidget(rect);
		jcp.listen('crop.change',(widget,e) => {
			x1 = widget.pos.x; y1 = widget.pos.y
			x2 = x1 + widget.pos.w; y2 = y1 + widget.pos.h
			img = $($(widget.el).parents().eq(1)).children("img")[0];
			w = img.width; h = img.height;
			x1 = x1/w; y1 = y1/h
			x2 = x2/w; y2 = y2/h
			div = $(widget.el).parents().eq(2);
			$(div).children("input[name$=xp1]").val(x1);
			$(div).children("input[name$=yp1]").val(y1);
			$(div).children("input[name$=xp2]").val(x2);
			$(div).children("input[name$=yp2]").val(y2);
			$(div).children("input[name$=checked]").val('True')
		});
		jcp.focus();
	});
});
